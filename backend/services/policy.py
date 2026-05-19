from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from backend.models.models import PromptNamespace, PromptVersion, Interaction, FeedbackSignal, IterationJob

class PolicyEngine:
    @staticmethod
    def should_iterate(db: Session, namespace_id) -> bool:
        """
        Evaluate gating policy to decide if APIS should optimize the prompt.
        """
        # 1. Fetch Namespace
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        if not namespace:
            return False
            
        policy = namespace.iteration_policy or {}
        min_signals = policy.get("min_signals", 50)
        min_negative_rate = policy.get("min_negative_rate", 0.35)
        cooldown_hours = policy.get("cooldown_hours", 24)
        
        # 2. Get Active Version
        active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == namespace_id,
            PromptVersion.status == "active"
        ).first()
        if not active_version:
            return False
            
        # 3. Check Cooldown
        # Query most recent successful or running iteration jobs
        cooldown_expired = True
        last_job = db.query(IterationJob).filter(
            IterationJob.namespace_id == namespace_id,
            IterationJob.status.in_(["completed", "running"])
        ).order_by(IterationJob.created_at.desc()).first()
        
        if last_job:
            job_created_at = last_job.created_at
            if job_created_at.tzinfo is None:
                # Naive to aware (assuming UTC)
                job_created_at = job_created_at.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            delta = now - job_created_at
            if delta < timedelta(hours=cooldown_hours):
                cooldown_expired = False
                
        # 4. Calculate total interactions & negative signals for this active version
        total_interactions = db.query(func.count(Interaction.id)).filter(
            Interaction.prompt_version_id == active_version.id
        ).scalar() or 0
        
        if total_interactions == 0:
            return False
            
        # Count all negative signals
        total_negative_signals = db.query(func.count(FeedbackSignal.id)).join(
            Interaction, FeedbackSignal.interaction_id == Interaction.id
        ).filter(
            Interaction.prompt_version_id == active_version.id,
            FeedbackSignal.signal_type.in_(["thumbs_down", "incorrect", "too_long", "too_short"])
        ).scalar() or 0
        
        negative_rate = float(total_negative_signals) / total_interactions
        
        # 5. Evaluate Decision Policy
        return (
            total_negative_signals >= min_signals
            and negative_rate >= min_negative_rate
            and cooldown_expired
        )
