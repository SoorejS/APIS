import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction, FeedbackSignal, DriftAlert
)
from backend.services.drift import DriftDetector

# Setup isolated database for verification
VERIFY_DB_URL = "sqlite:///./drift_verify.db"
engine_v = create_engine(VERIFY_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_v)

# Initialize tables
Base.metadata.drop_all(bind=engine_v)
Base.metadata.create_all(bind=engine_v)

def run_verification():
    db = SessionLocal()
    print("="*75)
    print("      APIS DRIFT DETECTION & ALERT QUALITY VERIFICATION")
    print("="*75 + "\n")

    now = datetime.datetime.now(datetime.timezone.utc)

    # ──────────────────────────────────────────────────────────────────────
    # TEST 1: GENUINE DRIFT DETECTION
    # ──────────────────────────────────────────────────────────────────────
    print("--- PART 1: Genuine Drift Detection ---")
    
    # Create namespace
    ns_genuine = PromptNamespace(name="ns-genuine-drift", constraints={}, iteration_policy={})
    db.add(ns_genuine)
    db.commit()
    db.refresh(ns_genuine)
    
    v1 = PromptVersion(namespace_id=ns_genuine.id, version_string="v1.0", content="Base", status="active")
    db.add(v1)
    db.commit()

    # Populate 30-day baseline (healthy, 15 days ago)
    print("  [+] Generating healthy historical baseline interactions (15 days ago)...")
    for _ in range(15):
        db.add(Interaction(
            namespace_id=ns_genuine.id,
            prompt_version_id=v1.id,
            user_query="How do I return this item?",
            ai_response="Navigate to orders and click return.",  # short, concise (36 chars)
            latency_ms=110,
            query_category="refunds",
            created_at=now - datetime.timedelta(days=15)
        ))
    db.commit()

    # Populate 7-day degradation (degraded, 2 days ago)
    print("  [!] Generating degraded recent interactions (2 days ago)...")
    for _ in range(5):
        interaction = Interaction(
            namespace_id=ns_genuine.id,
            prompt_version_id=v1.id,
            user_query="My order arrived broken.",
            ai_response="We deeply apologize for the inconvenience. Here is a very long, redundant explanation of our policy "
                        "regarding broken shipments, including how long it takes, terms and conditions, and other details "
                        "designed to represent excessive verbosity drift in the AI model outputs...",  # 256 chars
            latency_ms=480,  # latency spike (> 1.5x and > 100ms)
            query_category="refunds",
            created_at=now - datetime.timedelta(days=2)
        )
        db.add(interaction)
        db.commit()

        # Submit negative signals to represent thumbs_down & hallucination
        db.add(FeedbackSignal(interaction_id=interaction.id, signal_type="thumbs_down"))
        db.add(FeedbackSignal(interaction_id=interaction.id, signal_type="incorrect"))
    db.commit()

    # Trigger Drift Detection
    print("  [+] Running DriftDetector.detect_drift()...")
    alerts_genuine = DriftDetector.detect_drift(db, ns_genuine.id)
    
    print(f"  [+] Detected {len(alerts_genuine)} Drift Alerts:")
    for idx, alert in enumerate(alerts_genuine, 1):
        print(f"    Alert #{idx}: Type: {alert.drift_type:<14} | Severity: {alert.severity:<8} | Recommendation: {alert.recommendation}")
    
    # DB persistence check
    persisted_alerts = db.query(DriftAlert).filter(DriftAlert.namespace_id == ns_genuine.id).all()
    print(f"  [+] Database Verification: {len(persisted_alerts)} alerts successfully persisted in 'drift_alerts' table.")
    assert len(persisted_alerts) == 4
    print("  [+] PART 1 passed: All genuine drift trends successfully triggered and logged.\n")


    # ──────────────────────────────────────────────────────────────────────
    # TEST 2: FALSE POSITIVE RESISTANCE
    # ──────────────────────────────────────────────────────────────────────
    print("--- PART 2: False Positive Resistance ---")
    
    # Create noisy namespace
    ns_noisy = PromptNamespace(name="ns-noisy-baseline", constraints={}, iteration_policy={})
    db.add(ns_noisy)
    db.commit()
    db.refresh(ns_noisy)
    
    v2 = PromptVersion(namespace_id=ns_noisy.id, version_string="v1.0", content="Base", status="active")
    db.add(v2)
    db.commit()

    # Populate baseline (15 days ago)
    print("  [+] Generating healthy baseline interactions...")
    for _ in range(15):
        db.add(Interaction(
            namespace_id=ns_noisy.id,
            prompt_version_id=v2.id,
            user_query="Help?",
            ai_response="How can I help you today?",
            latency_ms=100,
            query_category="support",
            created_at=now - datetime.timedelta(days=15)
        ))
    db.commit()

    # Populate 7-day window with minor random fluctuation (no genuine degradation)
    print("  [+] Generating noisy recent interactions (minor fluctuation)...")
    for _ in range(5):
        db.add(Interaction(
            namespace_id=ns_noisy.id,
            prompt_version_id=v2.id,
            user_query="Help?",
            ai_response="How can I help you today, sir?",  # slightly longer but healthy
            latency_ms=105,  # minor fluctuation (105ms vs 100ms)
            query_category="support",
            created_at=now - datetime.timedelta(days=2)
        ))
    db.commit()

    # Trigger Drift Detection on noisy namespace
    print("  [+] Running DriftDetector.detect_drift()...")
    alerts_noisy = DriftDetector.detect_drift(db, ns_noisy.id)
    
    print(f"  [+] Detected {len(alerts_noisy)} Drift Alerts (Expected: 0).")
    
    assert len(alerts_noisy) == 0
    print("  [+] PART 2 passed: No false alerts triggered by random noise.\n")

    print("="*75)
    print("      VERIFICATION SUCCESS: ALL DRIFT ENGINE QUALITY TESTS PASSED")
    print("="*75)

    db.close()
    # Clean up database
    Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    run_verification()
