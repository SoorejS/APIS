import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.models import Interaction, FeedbackSignal, DriftAlert, PromptNamespace

class DriftDetector:
    @staticmethod
    def detect_drift(db: Session, namespace_id) -> list:
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        if not namespace:
            return []

        categories = db.query(Interaction.query_category).filter(
            Interaction.namespace_id == namespace_id
        ).distinct().all()
        categories = [c[0] for c in categories if c[0] is not None]
        if not categories:
            categories = ["general"]

        alerts = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for category in categories:
            metrics_1d = DriftDetector._get_window_metrics(db, namespace_id, category, now - datetime.timedelta(days=1))
            metrics_7d = DriftDetector._get_window_metrics(db, namespace_id, category, now - datetime.timedelta(days=7))
            metrics_30d = DriftDetector._get_window_metrics(db, namespace_id, category, now - datetime.timedelta(days=30))

            # 1. Thumbs down rate drift
            td_short = metrics_7d["thumbs_down_rate"]
            td_long = metrics_30d["thumbs_down_rate"]
            if metrics_7d["total_count"] >= 1 and td_short > td_long + 0.15:
                diff = td_short - td_long
                severity = "medium"
                recommendation = "monitor"
                if diff > 0.30:
                    severity = "critical"
                    recommendation = "rollback"
                elif diff > 0.20:
                    severity = "high"
                    recommendation = "iterate"
                
                alert = DriftDetector._create_alert(
                    db, namespace_id, category, "thumbs_down", severity, recommendation
                )
                alerts.append(alert)

            # 2. Latency drift
            lat_short = metrics_7d["avg_latency"]
            lat_long = metrics_30d["avg_latency"]
            if metrics_7d["total_count"] >= 1 and lat_long > 0 and lat_short > lat_long * 1.5:
                severity = "high" if lat_short > lat_long * 2.0 else "medium"
                recommendation = "iterate"
                alert = DriftDetector._create_alert(
                    db, namespace_id, category, "latency", severity, recommendation
                )
                alerts.append(alert)

            # 3. Verbosity drift
            verb_short = metrics_7d["avg_verbosity"]
            verb_long = metrics_30d["avg_verbosity"]
            if metrics_7d["total_count"] >= 1 and verb_long > 0 and verb_short > verb_long * 1.5:
                severity = "low" if verb_short < verb_long * 2.0 else "medium"
                recommendation = "iterate"
                alert = DriftDetector._create_alert(
                    db, namespace_id, category, "verbosity", severity, recommendation
                )
                alerts.append(alert)

            # 4. Hallucination drift (incorrect signals)
            hal_short = metrics_7d["incorrect_rate"]
            hal_long = metrics_30d["incorrect_rate"]
            if metrics_7d["total_count"] >= 1 and hal_short > hal_long + 0.10:
                severity = "critical" if hal_short > hal_long + 0.25 else "high"
                recommendation = "human_review"
                alert = DriftDetector._create_alert(
                    db, namespace_id, category, "hallucination", severity, recommendation
                )
                alerts.append(alert)

        return alerts

    @staticmethod
    def _get_window_metrics(db: Session, namespace_id, category: str, start_time: datetime.datetime) -> dict:
        stats = db.query(
            func.count(Interaction.id).label("total"),
            func.avg(Interaction.latency_ms).label("avg_latency"),
            func.avg(func.length(Interaction.ai_response)).label("avg_verbosity")
        ).filter(
            Interaction.namespace_id == namespace_id,
            Interaction.query_category == category,
            Interaction.created_at >= start_time
        ).first()

        total = stats.total if stats and stats.total else 0
        avg_latency = stats.avg_latency if stats and stats.avg_latency else 0.0
        avg_verbosity = stats.avg_verbosity if stats and stats.avg_verbosity else 0.0

        td_count = db.query(func.count(FeedbackSignal.id)).join(
            Interaction, FeedbackSignal.interaction_id == Interaction.id
        ).filter(
            Interaction.namespace_id == namespace_id,
            Interaction.query_category == category,
            Interaction.created_at >= start_time,
            FeedbackSignal.signal_type == "thumbs_down"
        ).scalar() or 0

        inc_count = db.query(func.count(FeedbackSignal.id)).join(
            Interaction, FeedbackSignal.interaction_id == Interaction.id
        ).filter(
            Interaction.namespace_id == namespace_id,
            Interaction.query_category == category,
            Interaction.created_at >= start_time,
            FeedbackSignal.signal_type == "incorrect"
        ).scalar() or 0

        return {
            "total_count": total,
            "avg_latency": avg_latency,
            "avg_verbosity": avg_verbosity,
            "thumbs_down_rate": td_count / total if total > 0 else 0.0,
            "incorrect_rate": inc_count / total if total > 0 else 0.0,
        }

    @staticmethod
    def _create_alert(db: Session, namespace_id, category: str, drift_type: str, severity: str, recommendation: str) -> DriftAlert:
        existing = db.query(DriftAlert).filter(
            DriftAlert.namespace_id == namespace_id,
            DriftAlert.category == category,
            DriftAlert.drift_type == drift_type,
            DriftAlert.resolved == False
        ).first()
        if existing:
            return existing

        alert = DriftAlert(
            namespace_id=namespace_id,
            category=category,
            drift_type=drift_type,
            severity=severity,
            recommendation=recommendation,
            resolved=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
