import os
import random
import time
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
VERIFY_DB_URL = "sqlite:///./canary_rollback_verify.db"
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
    print("="*70)
    print("      APIS CANARY ROLLBACK ATTACK MANUAL VERIFICATION")
    print("="*70 + "\n")

    # 1. Create fresh namespace
    namespace_name = "payment-gateway-service"
    namespace = PromptNamespace(
        name=namespace_name,
        constraints={"must_preserve": ["Helpful tone"]},
        iteration_policy={"provider": "gemini"}
    )
    db.add(namespace)
    db.commit()
    db.refresh(namespace)
    print(f"[1] Created namespace '{namespace_name}' (ID: {namespace.id})")

    # 2. Create and activate v1.0 baseline
    v1 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.0",
        content="You are a helpful AI assistant. Provide customer support.",
        status="active"
    )
    db.add(v1)
    db.commit()
    db.refresh(v1)
    print(f"[2] Created baseline version {v1.version_string} and marked ACTIVE")

    # 3. Create v1.1 candidate
    v2 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.1-candidate",
        content="Speak like a pirate. Arggh!",
        status="candidate"
    )
    db.add(v2)
    db.commit()
    db.refresh(v2)
    print(f"[3] Generated degraded candidate version {v2.version_string} (status: candidate)")

    # 4. Create prompt deployment entry
    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=v2.id,
        rollout_percentage=0,
        deployment_state="candidate"
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    print(f"[4] Initialized deployment entry in 'candidate' state, rollout: {deployment.rollout_percentage}%")

    # 5. Start rollout at canary_10
    deployment.deployment_state = "canary_10"
    deployment.rollout_percentage = 10
    db.commit()
    db.refresh(deployment)
    print(f"[5] Advanced state to 'canary_10', rollout: {deployment.rollout_percentage}%\n")

    # 6. Run stage 1 (canary_10) with some candidate traffic
    print(f"--- Running stage: canary_10 (rollout: {deployment.rollout_percentage}%) ---")
    print(f"  Simulating 50 queries routed via /generate API...")
    cand_count = 0
    base_count = 0
    
    for i in range(50):
        req_data = {
            "namespace": namespace_name,
            "query": "I want to pay my bill."
        }
        response = client.post("/api/v1/runtime/generate", json=req_data)
        assert response.status_code == 200
        res_json = response.json()
        interaction_id = res_json["interaction_id"]
        
        interaction = db.query(Interaction).filter(Interaction.id == uuid.UUID(interaction_id)).first()
        
        # Inject degraded performance:
        # If baseline: 95% thumbs_up, 5% thumbs_down
        # If candidate: 20% thumbs_up, 80% thumbs_down
        if interaction.prompt_version_id == v2.id:
            cand_count += 1
            signal_type = "thumbs_down" if random.random() < 0.80 else "thumbs_up"
        else:
            base_count += 1
            signal_type = "thumbs_up" if random.random() < 0.95 else "thumbs_down"
            
        feedback_res = client.post("/api/v1/feedback/", json={
            "interaction_id": str(interaction_id),
            "signal_type": signal_type
        })
        assert feedback_res.status_code == 200

    print(f"  Traffic distribution: Candidate: {cand_count} calls | Baseline: {base_count} calls")
    
    if cand_count < 3:
        print("  [!] Low candidate traffic. Simulating direct candidate interactions to ensure metric coverage...")
        for _ in range(5):
            cand_inter = Interaction(
                namespace_id=namespace.id,
                prompt_version_id=v2.id,
                user_query="How do I pay?",
                ai_response="Arggh, pay with doubloons!",
                latency_ms=120,
                provider="gemini",
                query_category="billing"
            )
            db.add(cand_inter)
            db.commit()
            
            db.add(FeedbackSignal(
                interaction_id=cand_inter.id,
                signal_type="thumbs_down"
            ))
            db.commit()
            cand_count += 1

    # 7. Evaluate deployment metrics
    db.refresh(deployment)
    metrics = CanaryService.evaluate_metrics(db, deployment.id)
    cand_metrics = metrics.get("candidate", {})
    base_metrics = metrics.get("baseline", {})
    
    print(f"  Evaluated database metrics:")
    print(f"    - Baseline: Total: {base_metrics.get('total_interactions')} | thumbs_down rate: {base_metrics.get('thumbs_down_rate'):.2%}")
    print(f"    - Candidate: Total: {cand_metrics.get('total_interactions')} | thumbs_down rate: {cand_metrics.get('thumbs_down_rate'):.2%}")
    
    # Run advancement check
    print(f"  Advancing rollout...")
    deployment = CanaryService.check_and_advance(db, deployment.id)
    print(f"  => Transitioned to State: {deployment.deployment_state} | Rollout: {deployment.rollout_percentage}%")
    print(f"  => Rollback Reason: {deployment.rollback_reason}\n")
    db.commit()

    # Verify final database persistence and active versions
    db.refresh(v1)
    db.refresh(v2)
    print("="*70)
    print("      FINAL DATABASE STATE VERIFICATION")
    print("="*70)
    print(f"Deployment state:          {deployment.deployment_state}")
    print(f"Deployment percentage:     {deployment.rollout_percentage}%")
    print(f"Rollback reason:           {deployment.rollback_reason}")
    print(f"Prompt v1.0 (baseline) status: {v1.status}")
    print(f"Prompt v1.1-candidate status:  {v2.status}")
    
    assert deployment.deployment_state == "rolled_back"
    assert deployment.rollout_percentage == 0
    assert v1.status == "active"
    assert v2.status == "candidate"
    print("\n[+] Verification SUCCESS: Degraded candidate rejected. Baseline preserved.")
    print("="*70)

    db.close()
    # Clean up database
    Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    run_verification()
