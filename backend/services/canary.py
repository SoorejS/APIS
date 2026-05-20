import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.models import PromptNamespace, PromptVersion, Interaction, FeedbackSignal, PromptDeployment

class CanaryService:
    @staticmethod
    def get_active_deployment(db: Session, namespace_id):
        return db.query(PromptDeployment).filter(
            PromptDeployment.namespace_id == namespace_id,
            PromptDeployment.deployment_state.in_(["canary_10", "canary_25", "canary_50"])
        ).first()

    @staticmethod
    def should_route_to_canary(deployment: PromptDeployment) -> bool:
        if not deployment:
            return False
        return random.randint(1, 100) <= deployment.rollout_percentage

    @staticmethod
    def evaluate_metrics(db: Session, deployment_id) -> dict:
        """
        Aggregate current metrics for the canary candidate version vs baseline version.
        Returns a dict of metrics.
        """
        deployment = db.query(PromptDeployment).filter(PromptDeployment.id == deployment_id).first()
        if not deployment:
            return {}

        namespace_id = deployment.namespace_id
        candidate_version_id = deployment.prompt_version_id

        # Active baseline version
        active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == namespace_id,
            PromptVersion.status == "active"
        ).first()

        if not active_version:
            return {}

        # Fetch stats for candidate
        cand_stats = db.query(
            func.count(Interaction.id).label("total"),
            func.avg(Interaction.latency_ms).label("avg_latency")
        ).filter(Interaction.prompt_version_id == candidate_version_id).first()

        # Fetch stats for baseline
        base_stats = db.query(
            func.count(Interaction.id).label("total"),
            func.avg(Interaction.latency_ms).label("avg_latency")
        ).filter(Interaction.prompt_version_id == active_version.id).first()

        # Fetch thumbs down counts
        cand_neg = db.query(func.count(FeedbackSignal.id)).join(
            Interaction, FeedbackSignal.interaction_id == Interaction.id
        ).filter(
            Interaction.prompt_version_id == candidate_version_id,
            FeedbackSignal.signal_type == "thumbs_down"
        ).scalar() or 0

        base_neg = db.query(func.count(FeedbackSignal.id)).join(
            Interaction, FeedbackSignal.interaction_id == Interaction.id
        ).filter(
            Interaction.prompt_version_id == active_version.id,
            FeedbackSignal.signal_type == "thumbs_down"
        ).scalar() or 0

        # Calculate rates
        cand_total = cand_stats.total if cand_stats and cand_stats.total else 0
        base_total = base_stats.total if base_stats and base_stats.total else 0

        cand_neg_rate = cand_neg / cand_total if cand_total > 0 else 0.0
        base_neg_rate = base_neg / base_total if base_total > 0 else 0.0

        cand_latency = cand_stats.avg_latency if cand_stats and cand_stats.avg_latency else 0.0
        base_latency = base_stats.avg_latency if base_stats and base_stats.avg_latency else 0.0

        metrics = {
            "baseline": {
                "total_interactions": base_total,
                "thumbs_down_rate": base_neg_rate,
                "avg_latency_ms": base_latency,
                "correctness": 1.0,
                "category_regression": False
            },
            "candidate": {
                "total_interactions": cand_total,
                "thumbs_down_rate": cand_neg_rate,
                "avg_latency_ms": cand_latency,
                "correctness": 1.0,
                "category_regression": False
            }
        }
        return metrics

    @staticmethod
    def check_and_advance(db: Session, deployment_id, custom_metrics: dict = None) -> PromptDeployment:
        """
        Evaluate metrics. If regression detected, perform automatic rollback.
        Otherwise, promote to next state (canary_10 -> canary_25 -> canary_50 -> active).
        """
        deployment = db.query(PromptDeployment).filter(PromptDeployment.id == deployment_id).first()
        if not deployment:
            return None

        # Determine metrics to use
        metrics = custom_metrics or CanaryService.evaluate_metrics(db, deployment_id)
        if not metrics:
            return deployment

        deployment.current_metrics = metrics.get("candidate", {})
        deployment.baseline_metrics = metrics.get("baseline", {})

        # Evaluate rollback conditions
        cand_metrics = metrics.get("candidate", {})
        base_metrics = metrics.get("baseline", {})

        cand_neg = cand_metrics.get("thumbs_down_rate", 0.0)
        base_neg = base_metrics.get("thumbs_down_rate", 0.0)

        cand_lat = cand_metrics.get("avg_latency_ms", 0.0)
        base_lat = base_metrics.get("avg_latency_ms", 0.0)

        # Rollback conditions
        rollback = False
        reason = ""

        # 1. Thumbs down rate increases significantly (e.g. margin of 10%)
        if cand_neg > base_neg + 0.10:
            rollback = True
            reason = f"thumbs_down rate increased (candidate: {cand_neg:.2f} vs baseline: {base_neg:.2f})"
        
        # 2. Correctness score decreases significantly
        elif cand_metrics.get("correctness", 1.0) < base_metrics.get("correctness", 1.0) - 0.10:
            rollback = True
            reason = f"correctness score dropped (candidate: {cand_metrics.get('correctness'):.2f} vs baseline: {base_metrics.get('correctness'):.2f})"

        # 3. Latency increases significantly (more than 50% increase AND more than 100ms)
        elif cand_lat > base_lat * 1.5 and (cand_lat - base_lat) > 100:
            rollback = True
            reason = f"latency increased significantly (candidate: {cand_lat:.1f}ms vs baseline: {base_lat:.1f}ms)"

        # 4. Specific category regressions
        elif cand_metrics.get("category_regression", False):
            rollback = True
            reason = "detected regression in key query category"

        if rollback:
            deployment.deployment_state = "rolled_back"
            deployment.rollout_percentage = 0
            deployment.rollback_reason = reason
            db.commit()
            db.refresh(deployment)
            return deployment

        # Otherwise promote
        current_state = deployment.deployment_state
        if current_state in ["candidate", "evaluating"]:
            deployment.deployment_state = "canary_10"
            deployment.rollout_percentage = 10
        elif current_state == "canary_10":
            deployment.deployment_state = "canary_25"
            deployment.rollout_percentage = 25
        elif current_state == "canary_25":
            deployment.deployment_state = "canary_50"
            deployment.rollout_percentage = 50
        elif current_state == "canary_50":
            deployment.deployment_state = "active"
            deployment.rollout_percentage = 100
            
            # Deactivate previous active version
            active_version = db.query(PromptVersion).filter(
                PromptVersion.namespace_id == deployment.namespace_id,
                PromptVersion.status == "active"
            ).first()
            if active_version:
                active_version.status = "archived"

            # Set candidate version to active
            candidate_version = db.query(PromptVersion).filter(
                PromptVersion.id == deployment.prompt_version_id
            ).first()
            if candidate_version:
                candidate_version.status = "active"
        
        db.commit()
        db.refresh(deployment)
        return deployment
