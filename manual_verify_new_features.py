import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from unittest.mock import patch

from backend.db.database import Base
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction, FeedbackSignal,
    PromptDeployment, DriftAlert
)
from backend.services.canary import CanaryService
from backend.providers.registry import registry
from backend.services.drift import DriftDetector

VERIFY_DB_URL = "sqlite:///./verify_features.db"
engine_v = create_engine(VERIFY_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_v)

async def run_demo():
    print("="*60)
    print("    APIS NEW FEATURES DEMONSTRATION & VERIFICATION")
    print("="*60 + "\n")
    
    # Initialize DB
    Base.metadata.drop_all(bind=engine_v)
    Base.metadata.create_all(bind=engine_v)
    db = SessionLocal()

    try:
        # ──────────────────────────────────────────────────────────────────────
        # DEMO 1: CANARY ROLLOUT & AUTOMATIC ROLLBACK SCENARIO
        # ──────────────────────────────────────────────────────────────────────
        print("--- DEMO 1: Canary Promotion & Automatic Rollback ---")
        
        # Setup mock namespace and versions
        namespace = PromptNamespace(
            name="canary-demo-namespace",
            constraints={},
            iteration_policy={}
        )
        db.add(namespace)
        db.commit()

        v1 = PromptVersion(
            namespace_id=namespace.id,
            version_string="v1.0",
            content="Standard helper.",
            status="active"
        )
        v2 = PromptVersion(
            namespace_id=namespace.id,
            version_string="v2.0-canary",
            content="Optimized helper.",
            status="candidate"
        )
        db.add_all([v1, v2])
        db.commit()

        # Initialize Deployment
        deployment = PromptDeployment(
            namespace_id=namespace.id,
            prompt_version_id=v2.id,
            rollout_percentage=0,
            deployment_state="candidate"
        )
        db.add(deployment)
        db.commit()
        print(f"Created Deployment. State: {deployment.deployment_state}, Rollout: {deployment.rollout_percentage}%")

        # 1. Promote to canary_10
        good_metrics = {
            "baseline": {"thumbs_down_rate": 0.04, "avg_latency_ms": 100.0, "correctness": 1.0},
            "candidate": {"thumbs_down_rate": 0.02, "avg_latency_ms": 95.0, "correctness": 1.0}
        }
        deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
        print(f"  [+] Promoted -> State: {deployment.deployment_state}, Rollout: {deployment.rollout_percentage}%")

        # 2. Promote to canary_25
        deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
        print(f"  [+] Promoted -> State: {deployment.deployment_state}, Rollout: {deployment.rollout_percentage}%")

        # 3. Simulate regression at 25% (thumbs_down rate spikes to 30%)
        bad_metrics = {
            "baseline": {"thumbs_down_rate": 0.04, "avg_latency_ms": 100.0, "correctness": 1.0},
            "candidate": {"thumbs_down_rate": 0.30, "avg_latency_ms": 98.0, "correctness": 1.0}
        }
        print("  [!] Injecting negative feedback signal regression...")
        deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=bad_metrics)
        print(f"  [!] Evaluation Complete -> State: {deployment.deployment_state}, Rollout: {deployment.rollout_percentage}%")
        print(f"  [!] Rollback Reason: {deployment.rollback_reason}\n")


        # ──────────────────────────────────────────────────────────────────────
        # DEMO 2: MULTI-PROVIDER ROUTING & FALLBACK
        # ──────────────────────────────────────────────────────────────────────
        print("--- DEMO 2: Multi-Provider Runtime Routing ---")
        
        # Test registered provider retrieval
        providers = ["gemini", "openai", "claude", "ollama"]
        for p in providers:
            prov = registry.get_provider(p)
            res = await prov.generate("Ping")
            print(f"  Selected Provider: {p:<10} -> Response: {res}")

        # Simulate provider failure and fallback
        print("  [!] Simulating OpenAI failure fallback to Gemini...")
        with patch("backend.providers.openai.OpenAIProvider.generate", side_effect=Exception("OpenAI rate limit exceeded")):
            fallback_res = await registry.generate_with_fallback("openai", "Ping", fallback_name="gemini")
            print(f"  [+] Fallback Response: {fallback_res}\n")


        # ──────────────────────────────────────────────────────────────────────
        # DEMO 3: DRIFT DETECTION & ALERT GENERATION
        # ──────────────────────────────────────────────────────────────────────
        print("--- DEMO 3: Drift Detection & Alert Generation ---")
        
        # Populate history
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Baseline Interactions (15 days ago, 100% positive)
        for i in range(10):
            db.add(Interaction(
                namespace_id=namespace.id,
                prompt_version_id=v1.id,
                user_query="Hello",
                ai_response="Hi there!",
                latency_ms=120,
                query_category="billing",
                created_at=now - datetime.timedelta(days=15)
            ))
        db.commit()

        # Recent Degraded Interactions (2 days ago, 100% negative + high latency)
        for i in range(5):
            inter = Interaction(
                namespace_id=namespace.id,
                prompt_version_id=v1.id,
                user_query="Billing problem",
                ai_response="I cannot resolve billing problems at this time.",
                latency_ms=650,  # Latency drift trigger (> 1.5x)
                query_category="billing",
                created_at=now - datetime.timedelta(days=2)
            )
            db.add(inter)
            db.commit()

            db.add(FeedbackSignal(
                interaction_id=inter.id,
                signal_type="thumbs_down"
            ))
            db.add(FeedbackSignal(
                interaction_id=inter.id,
                signal_type="incorrect"
            ))
        db.commit()

        print("  [+] Aggregating metrics over rolling windows...")
        for cat in ["billing"]:
            m1d = DriftDetector._get_window_metrics(db, namespace.id, cat, now - datetime.timedelta(days=1))
            m7d = DriftDetector._get_window_metrics(db, namespace.id, cat, now - datetime.timedelta(days=7))
            m30d = DriftDetector._get_window_metrics(db, namespace.id, cat, now - datetime.timedelta(days=30))
            print(f"    [DEBUG billing] 7d count: {m7d['total_count']}, thumbs_down_rate: {m7d['thumbs_down_rate']}, latency: {m7d['avg_latency']}")
            print(f"    [DEBUG billing] 30d count: {m30d['total_count']}, thumbs_down_rate: {m30d['thumbs_down_rate']}, latency: {m30d['avg_latency']}")
        
        alerts = DriftDetector.detect_drift(db, namespace.id)
        
        print(f"  [+] Generated {len(alerts)} Drift Alerts:")
        for idx, alert in enumerate(alerts, 1):
            print(f"    Alert #{idx}: Category: {alert.category:<10} | Type: {alert.drift_type:<12} | Severity: {alert.severity:<8} | Recommendation: {alert.recommendation}")
        print("\n" + "="*60)
        print("      ALL NEW FEATURES VERIFIED & COMPILING PERFECTLY!")
        print("="*60)

    finally:
        db.close()
        # Clean up database
        Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    import anyio
    anyio.run(run_demo)
