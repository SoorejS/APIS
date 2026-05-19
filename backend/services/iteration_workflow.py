from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import traceback

from backend.models.models import IterationJob, PromptNamespace, PromptVersion, QualityPattern
from backend.services.signal_engine import SignalEngine
from backend.services.policy import PolicyEngine
from backend.services.iteration import IterationEngine
from backend.services.diff_engine import PromptDiffEngine

class IterationWorkflow:
    @staticmethod
    async def run_iteration_flow(db: Session, namespace_id: uuid.UUID) -> IterationJob:
        """
        Runs the full end-to-end adaptive prompt iteration workflow:
        1. Run SignalEngine to detect any recurring problems.
        2. Evaluate gating policy via ShouldIterate().
        3. If true, start the iteration job.
        4. Query LLM to generate optimized candidate prompt.
        5. Calculate differential.
        6. Persist version and update job status.
        """
        # 1. Verify Namespace
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        if not namespace:
            raise ValueError(f"Namespace {namespace_id} not found.")
            
        # Get active version
        active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == namespace_id,
            PromptVersion.status == "active"
        ).first()
        if not active_version:
            raise ValueError(f"No active prompt version found for namespace {namespace_id}.")
            
        # 2. Trigger Signal Engine & Policy Check
        active_patterns = SignalEngine.aggregate_and_detect(db, namespace_id)
        should_iterate = PolicyEngine.should_iterate(db, namespace_id)
        
        if not should_iterate:
            # We don't need to iterate. Return None or a rejected job.
            print(f"[IterationWorkflow] Policy gating: ShouldIterate() = False. Skipping cycle.")
            return None
            
        # 3. Create Iteration Job
        job = IterationJob(
            namespace_id=namespace_id,
            prompt_version_id=active_version.id,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # 4. Execute Job
        job.status = "running"
        db.commit()
        try:
            # Call Iteration Engine
            candidate_content, rationale = await IterationEngine.generate_candidate(
                db=db,
                namespace_id=namespace_id,
                current_version=active_version,
                active_patterns=active_patterns
            )
            
            # Normalize structure, deduplicate guidelines/constraints, and enforce length budget
            from backend.services.normalizer import PromptNormalizerService
            candidate_content = PromptNormalizerService.normalize(candidate_content)
            
            # Reject empty/no-op prompt rewrites
            if not candidate_content or candidate_content.strip() == active_version.content.strip():
                raise ValueError("Candidate prompt generation produced an empty or no-op prompt rewrite.")
                
            # Generate diff
            diff_summary = PromptDiffEngine.generate_diff(active_version.content, candidate_content)
            
            # Calculate next candidate version string
            # Try to increment active version if it matches vX.Y, else use dynamic name
            try:
                ver_parts = active_version.version_string.split(".")
                major = int(ver_parts[0].replace("v", ""))
                minor = int(ver_parts[1])
                candidate_ver_str = f"v{major}.{minor + 1}-candidate"
            except Exception:
                candidate_ver_str = f"{active_version.version_string}-candidate"
                
            # 5. Persist Candidate Version
            candidate_version = PromptVersion(
                namespace_id=namespace_id,
                version_string=candidate_ver_str,
                content=candidate_content,
                status="candidate",
                parent_version_id=active_version.id,
                change_rationale=rationale,
                diff_summary=diff_summary
            )
            db.add(candidate_version)
            db.commit()
            db.refresh(candidate_version)
            
            # 6. Complete Job
            job.candidate_version_id = candidate_version.id
            job.status = "completed"
            db.commit()
            db.refresh(job)
            
            print(f"[IterationWorkflow] Successfully completed job {job.id}. Candidate: {candidate_ver_str}")
            return job
            
        except Exception as e:
            db.rollback()
            tb = traceback.format_exc()
            job.status = "failed"
            job.error_message = f"Error: {str(e)}\n\nTraceback:\n{tb}"
            db.commit()
            db.refresh(job)
            print(f"[IterationWorkflow] Job {job.id} failed: {e}")
            return job
