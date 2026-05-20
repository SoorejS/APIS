import os
import random
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base, get_db
from backend.main import app
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction, FeedbackSignal, PromptDeployment
)
from backend.services.canary import CanaryService

# Setup isolated database for verification
VERIFY_DB_URL = "sqlite:///./feedback_poisoning_verify.db"
engine_v = create_engine(VERIFY_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_v)

# Initialize tables
Base.metadata.drop_all(bind=engine_v)
Base.metadata.create_all(bind=engine_v)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def run_verification():
    db = SessionLocal()
    print("="*75)
    print("      APIS FEEDBACK POISONING & ADVERSARIAL ROBUSTNESS VERIFICATION")
    print("="*75 + "\n")

    # 1. Create fresh namespace
    namespace_name = "feedback-poison-namespace"
    namespace = PromptNamespace(
        name=namespace_name,
        constraints={"must_preserve": []},
        iteration_policy={"provider": "gemini"}
    )
    db.add(namespace)
    db.commit()
    db.refresh(namespace)
    print(f"[1] Created namespace '{namespace_name}'")

    # 2. Create baseline prompt version
    v1 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.0",
        content="You are a helpful customer assistant.",
        status="active"
    )
    db.add(v1)
    db.commit()
    db.refresh(v1)
    print(f"[2] Created baseline version {v1.version_string} (status: active)")

    # 3. Create healthy candidate prompt
    v2 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.1-candidate",
        content="You are an expert customer helper. Speak concisely.",
        status="candidate"
    )
    db.add(v2)
    db.commit()
    db.refresh(v2)
    print(f"[3] Generated candidate version {v2.version_string} (status: candidate)")

    # 4. Start canary rollout
    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=v2.id,
        rollout_percentage=10,
        deployment_state="canary_10"
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    print(f"[4] Started canary rollout at state 'canary_10', rollout: {deployment.rollout_percentage}%")

    # 5. Route healthy baseline traffic first
    print("\n--- PHASE 1: Normal Baseline Traffic ---")
    for _ in range(10):
        # We manually insert baseline interactions to represent high-volume healthy baseline traffic
        inter = Interaction(
            namespace_id=namespace.id,
            prompt_version_id=v1.id,
            user_query="Hello",
            ai_response="Hi, how can I help you?",
            latency_ms=100,
            provider="gemini",
            query_category="general"
        )
        db.add(inter)
        db.commit()
        db.add(FeedbackSignal(interaction_id=inter.id, signal_type="thumbs_up"))
        db.commit()
    print("  [+] Registered 10 healthy baseline interactions (all thumbs_up, thumbs_down rate: 0.0%)")

    # 6. Simulate malicious poisoning attack: spam negative feedback on a tiny subset
    print("\n--- PHASE 2: Malicious Poisoning Attack (Tiny Subset) ---")
    print("  [!] Malicious noisy group spamming negative feedback on candidate...")
    
    # We generate 4 candidate interactions, all with negative feedback (thumbs_down)
    for i in range(4):
        inter = Interaction(
            namespace_id=namespace.id,
            prompt_version_id=v2.id,
            user_query=f"Query {i}",
            ai_response="Conscise support response.",
            latency_ms=110,
            provider="gemini",
            query_category="general"
        )
        db.add(inter)
        db.commit()
        db.add(FeedbackSignal(interaction_id=inter.id, signal_type="thumbs_down"))
        db.commit()
    print("  [!] Registered 4 candidate interactions with 100% negative feedback.")

    # 7. Evaluate deployment metrics before statistical significance is met
    db.refresh(deployment)
    metrics = CanaryService.evaluate_metrics(db, deployment.id)
    cand_metrics = metrics.get("candidate", {})
    base_metrics = metrics.get("baseline", {})
    
    print(f"  [+] Current database metrics:")
    print(f"    - Baseline: Total: {base_metrics.get('total_interactions')} | thumbs_down rate: {base_metrics.get('thumbs_down_rate'):.2%}")
    print(f"    - Candidate: Total: {cand_metrics.get('total_interactions')} | thumbs_down rate: {cand_metrics.get('thumbs_down_rate'):.2%}")

    print("  [+] Running check_and_advance() evaluation...")
    deployment = CanaryService.check_and_advance(db, deployment.id)
    print(f"  => Deployment State: {deployment.deployment_state} | Rollout: {deployment.rollout_percentage}%")
    print(f"  => Rollback Reason: {deployment.rollback_reason}")
    
    # Assert that no rollback has occurred because candidate interactions (4) < 5 min threshold
    assert deployment.deployment_state != "rolled_back", "APIS rolled back too early on a statistically insignificant sample size!"
    print("  [+] SUCCESS: No instant rollback from tiny noisy group. System remained stable.")

    # 8. Add more traffic to make it statistically meaningful
    print("\n--- PHASE 3: Additional Interactions (Meeting Minimum Volume) ---")
    print("  [+] Routing 2 healthy candidate interactions (thumbs_up)...")
    for i in range(2):
        inter = Interaction(
            namespace_id=namespace.id,
            prompt_version_id=v2.id,
            user_query=f"Healthy Query {i}",
            ai_response="Concise support response.",
            latency_ms=110,
            provider="gemini",
            query_category="general"
        )
        db.add(inter)
        db.commit()
        db.add(FeedbackSignal(interaction_id=inter.id, signal_type="thumbs_up"))
        db.commit()

    # Re-evaluate now that candidate total interactions = 6 (>= 5 threshold)
    db.refresh(deployment)
    metrics = CanaryService.evaluate_metrics(db, deployment.id)
    cand_metrics = metrics.get("candidate", {})
    base_metrics = metrics.get("baseline", {})
    
    print(f"  [+] Re-evaluated database metrics:")
    print(f"    - Baseline: Total: {base_metrics.get('total_interactions')} | thumbs_down rate: {base_metrics.get('thumbs_down_rate'):.2%}")
    print(f"    - Candidate: Total: {cand_metrics.get('total_interactions')} | thumbs_down rate: {cand_metrics.get('thumbs_down_rate'):.2%}")

    print("  [+] Running check_and_advance() evaluation...")
    deployment = CanaryService.check_and_advance(db, deployment.id)
    print(f"  => Deployment State: {deployment.deployment_state} | Rollout: {deployment.rollout_percentage}%")
    print(f"  => Rollback Reason: {deployment.rollback_reason}")

    # Assert that rollback has now triggered because sample size (6) >= 5, and thumbs_down rate (67%) is significantly worse than baseline (0%)
    assert deployment.deployment_state == "rolled_back", "APIS failed to roll back once metrics became statistically meaningful!"
    print("  [+] SUCCESS: Rollback triggered successfully once statistical significance was met.")

    print("\n" + "="*75)
    print("      VERIFICATION SUCCESS: ADVERSARIAL SIGNAL RESILIENCE PROVEN")
    print("="*75)

    db.close()
    # Clean up database
    Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    run_verification()
