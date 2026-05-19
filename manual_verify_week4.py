import asyncio
import time
import os
import psycopg2
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.experiments.runner import ExperimentRunner
from backend.experiments.report_generator import ReportGenerator
from backend.services.evaluator import EvaluatorService
from backend.services.failure_memory import FailureMemoryService
from backend.models.models import PromptNamespace, PromptVersion, Base
from backend.db.database import SessionLocal

async def main():
    print("="*80)
    print("APIS MVP WEEK 4 - EXPERIMENTAL VALIDATION & CREDIBILITY RUNNER")
    print("="*80)
    
    # ── Setup database session ──
    db = SessionLocal()
    
    try:
        # 1. Register experimental namespaces in PostgreSQL
        print("\n[Step 1] Initializing production domains in PostgreSQL database...")
        domains = ["customer_support", "coding_assistant", "research_assistant"]
        namespaces = {}
        
        for d in domains:
            ns_name = f"{d}-exp-domain"
            # Cleanup existing to ensure clean run with proper referential integrity order
            existing = db.query(PromptNamespace).filter(PromptNamespace.name == ns_name).first()
            if existing:
                from backend.models.models import EvaluationRun, FailureMemory, Interaction, IterationJob
                # 1. Delete dependent tables
                db.query(EvaluationRun).filter(EvaluationRun.namespace_id == existing.id).delete()
                db.query(FailureMemory).filter(FailureMemory.namespace_id == existing.id).delete()
                db.query(IterationJob).filter(IterationJob.namespace_id == existing.id).delete()
                db.query(Interaction).filter(Interaction.namespace_id == existing.id).delete()
                # 2. Delete versions and namespace
                db.query(PromptVersion).filter(PromptVersion.namespace_id == existing.id).delete()
                db.query(PromptNamespace).filter(PromptNamespace.id == existing.id).delete()
                db.commit()
                
            ns = PromptNamespace(
                name=ns_name,
                description=f"Controlled Experiment domain for {d}",
                constraints={"must_preserve": ["Safety safeguards"], "cannot_modify": ["Max timeout limits"]},
                iteration_policy={"min_signals": 1, "min_negative_rate": 0.1, "cooldown_hours": 1}
            )
            db.add(ns)
            db.commit()
            db.refresh(ns)
            namespaces[d] = ns
            print(f"--> Initialized Namespace '{ns_name}': ID={ns.id}")
            
            # Setup active v1.0 and candidate v1.1 versions
            active_ver = PromptVersion(
                namespace_id=ns.id,
                version_string="v1.0",
                content=ExperimentRunner.BASELINES[d],
                status="active"
            )
            candidate_ver = PromptVersion(
                namespace_id=ns.id,
                version_string="v1.1-candidate",
                content=ExperimentRunner.ADAPTIVES[d],
                status="candidate",
                change_rationale="Experimental optimization of prompt guidelines."
            )
            db.add(active_ver)
            db.add(candidate_ver)
            db.commit()
            
        # 2. Run baseline vs adaptive experiments over all domains
        print("\n[Step 2] Launching Controlled Experiments comparing Baseline Static vs APIS Adaptive...")
        results = []
        for d in domains:
            res = await ExperimentRunner.run_experiment(
                db=db,
                domain=d,
                sample_size=100  # Evaluate over all 100 benchmark queries for absolute statistical rigor
            )
            results.append(res)
            
        # 3. Generate structured performance reports (results.json & results.md)
        print("\n[Step 3] Compiling and generating GFM performance reports...")
        json_path, md_path = ReportGenerator.generate_reports(results, output_dir=".")
        print(f"--> [SUCCESS] JSON results saved to: {os.path.abspath(json_path)}")
        print(f"--> [SUCCESS] Markdown results saved to: {os.path.abspath(md_path)}")
        
        # 4. Trigger Regression & Rejection to populate Failure Memory
        print("\n[Step 4] Triggering Evaluator Gated Rejection to verify Failure Memory pipeline...")
        # We will trigger a simulated coding regression for coding_assistant namespace
        coding_ns = namespaces["coding_assistant"]
        candidate_ver = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == coding_ns.id,
            PromptVersion.version_string == "v1.1-candidate"
        ).first()
        
        print(f"--> Launching evaluation with simulated regression of -4% on coding helper category...")
        eval_run = await EvaluatorService.run_offline_evaluation(
            db=db,
            namespace_id=coding_ns.id,
            candidate_version_id=candidate_ver.id,
            simulate_regression=True
        )
        print(f"--> Evaluator Decision: {eval_run.decision.upper()}")
        
        # 5. Assert Failure Memory persistence in PostgreSQL
        print("\n[Step 5] Checking failure memories in PostgreSQL database...")
        failures = FailureMemoryService.get_failures(db, coding_ns.id)
        assert len(failures) > 0, "Failure memory should contain at least one rejected record!"
        print(f"[OK] Database verified: Found {len(failures)} historical failure record in PostgreSQL.")
        for idx, f in enumerate(failures):
            print(f"    Failure #{idx+1}:")
            print(f"    - Pattern: '{f.failed_pattern}'")
            print(f"    - Attempted Fix: '{f.attempted_fix}'")
            print(f"    - Reason: '{f.reason}'")
            
        # 6. Verify that subsequent candidate generation retrieves failures to avoid repeat degradation
        print("\n[Step 6] Verifying Failure Memory injection into subsequent Iteration prompts...")
        failure_prompt = FailureMemoryService.get_formatted_failures_prompt(db, coding_ns.id)
        assert "HISTORICAL FAILURE MEMORY" in failure_prompt
        print("[OK] Verified Failure Memory Prompt formatting. Output preview:")
        print("-" * 60)
        print(failure_prompt.strip())
        print("-" * 60)
        
        # 7. Print compiled markdown report contents for absolute transparency
        print("\n[Step 7] Completed experimental report preview:")
        print("="*80)
        with open(md_path, "r") as f:
            print(f.read().strip())
        print("="*80)
        
        print("\n" + "="*80)
        print("SUCCESS: WEEK 4 EXPERIMENTAL VALIDATION ENGINE FULLY PROVEN END-TO-END!")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
