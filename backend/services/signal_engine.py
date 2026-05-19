from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.models import Interaction, FeedbackSignal, QualityPattern, PromptNamespace

class SignalEngine:
    @staticmethod
    def aggregate_and_detect(db: Session, namespace_id) -> list:
        """
        Aggregate feedback signals from PostgreSQL.
        Detect recurring quality patterns and persist them.
        """
        # 1. Fetch Namespace
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        if not namespace:
            return []
            
        policy = namespace.iteration_policy or {}
        min_signals = policy.get("min_signals", 5)
        min_negative_rate = policy.get("min_negative_rate", 0.30)
        
        # 2. Get interaction counts for namespace/version/category to serve as denominators
        interaction_counts = db.query(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            func.count(Interaction.id).label("total_interactions")
        ).filter(Interaction.namespace_id == namespace_id).group_by(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category
        ).all()
        
        int_map = {
            (row.namespace_id, row.prompt_version_id, row.query_category): row.total_interactions
            for row in interaction_counts
        }
        
        # 3. Get feedback signal counts grouped by version, category, and signal type
        signal_counts = db.query(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            FeedbackSignal.signal_type,
            func.count(FeedbackSignal.id).label("signal_count")
        ).join(
            FeedbackSignal, FeedbackSignal.interaction_id == Interaction.id
        ).filter(Interaction.namespace_id == namespace_id).group_by(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            FeedbackSignal.signal_type
        ).all()
        
        detected_patterns = []
        
        # 4. Analyze each aggregated signal group
        for row in signal_counts:
            total_int = int_map.get((row.namespace_id, row.prompt_version_id, row.query_category), 0)
            if total_int == 0:
                continue
                
            signal_count = row.signal_count
            negative_rate = float(signal_count) / total_int
            confidence = min(1.0, float(signal_count) / 100.0)
            
            # Simple check if this signal constitutes a quality pattern
            # Negative feedback signals: thumbs_down, incorrect, too_long, etc.
            is_negative_signal = row.signal_type in ["thumbs_down", "incorrect", "too_long", "too_short"]
            
            if is_negative_signal and signal_count >= min_signals and negative_rate >= min_negative_rate:
                # We have detected a pattern! Persist/Update in quality_patterns
                pattern = db.query(QualityPattern).filter(
                    QualityPattern.namespace_id == namespace_id,
                    QualityPattern.prompt_version_id == row.prompt_version_id,
                    QualityPattern.query_category == row.query_category,
                    QualityPattern.signal_type == row.signal_type
                ).first()
                
                if not pattern:
                    pattern = QualityPattern(
                        namespace_id=namespace_id,
                        prompt_version_id=row.prompt_version_id,
                        pattern_type="high_negative_feedback",
                        query_category=row.query_category,
                        signal_type=row.signal_type,
                        negative_rate=negative_rate,
                        signal_count=signal_count,
                        confidence=confidence,
                        status="active"
                    )
                    db.add(pattern)
                else:
                    pattern.negative_rate = negative_rate
                    pattern.signal_count = signal_count
                    pattern.confidence = confidence
                    pattern.status = "active"
                    
                db.commit()
                db.refresh(pattern)
                detected_patterns.append(pattern)
                
        return detected_patterns
        
    @staticmethod
    def get_aggregated_metrics(db: Session, namespace_id) -> list:
        """
        Get flat list of dict representations of aggregated feedback.
        """
        # Dynamic denominator calculation
        interaction_counts = db.query(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            func.count(Interaction.id).label("total_interactions")
        ).filter(Interaction.namespace_id == namespace_id).group_by(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category
        ).all()
        
        int_map = {
            (row.namespace_id, row.prompt_version_id, row.query_category): row.total_interactions
            for row in interaction_counts
        }
        
        signal_counts = db.query(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            FeedbackSignal.signal_type,
            func.count(FeedbackSignal.id).label("signal_count")
        ).join(
            FeedbackSignal, FeedbackSignal.interaction_id == Interaction.id
        ).filter(Interaction.namespace_id == namespace_id).group_by(
            Interaction.namespace_id,
            Interaction.prompt_version_id,
            Interaction.query_category,
            FeedbackSignal.signal_type
        ).all()
        
        results = []
        for row in signal_counts:
            total_int = int_map.get((row.namespace_id, row.prompt_version_id, row.query_category), 0)
            neg_rate = float(row.signal_count) / total_int if total_int > 0 else 0.0
            conf = min(1.0, float(row.signal_count) / 100.0)
            
            results.append({
                "namespace_id": str(row.namespace_id),
                "prompt_version_id": str(row.prompt_version_id),
                "query_category": row.query_category,
                "signal_type": row.signal_type,
                "negative_rate": neg_rate,
                "signal_count": row.signal_count,
                "confidence": conf
            })
        return results
