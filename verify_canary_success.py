import os
import random
import time
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
VERIFY_DB_URL = "sqlite:///./canary_success_verify.db"
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
    print("      APIS CANARY SUCCESS PATH MANUAL VERIFICATION")
    print("="*70 + "\n")

    # 1. Create fresh namespace
    namespace_name = "production-checkout-service"
    namespace = PromptNamespace(
        name=namespace_name,
        constraints={"must_preserve": ["Concise formatting", "Helpful tone"]},
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
        content="You are a helpful assistant. Keep responses under 2 sentences.",
        status="candidate"
    )
    db.add(v2)
    db.commit()
    db.refresh(v2)
    print(f"[3] Generated candidate version {v2.version_string} (status: candidate)")

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

    # 6. Progressive Rollout loop
    stages = ["canary_10", "canary_25", "canary_50"]
    for idx, stage in enumerate(stages):
        print(f"--- Running stage: {stage} (rollout: {deployment.rollout_percentage}%) ---")
        
        # Simulate 40 interactions routed through runtime
        print(f"  Simulating 40 queries routed via /generate API...")
        cand_count = 0
        base_count = 0
        
        for _ in range(40):
            req_data = {
                "namespace": namespace_name,
                "query": "I need help with my refund status."
            }
            # POST to runtime generate
            response = client.post("/api/v1/runtime/generate", json=req_data)
            assert response.status_code == 200
            res_json = response.json()
            interaction_id = res_json["interaction_id"]
            
            # Fetch the generated interaction to see which prompt version it routed to
            import uuid
            interaction = db.query(Interaction).filter(Interaction.id == uuid.UUID(interaction_id)).first()
            
            # Submit positive/negative feedback
            # 95% chance of thumbs_up (positive), 5% chance of thumbs_down (negative)
            signal_type = "thumbs_up" if random.random() < 0.95 else "thumbs_down"
            feedback_res = client.post("/api/v1/feedback/", json={
                "interaction_id": str(interaction_id),
                "signal_type": signal_type
            })
            assert feedback_res.status_code == 200
            
            if interaction.prompt_version_id == v2.id:
                cand_count += 1
            else:
                base_count += 1

        print(f"  Traffic distribution: Candidate: {cand_count} calls | Baseline: {base_count} calls")
        
        # 7. Evaluate deployment metrics
        db.refresh(deployment)
        metrics = CanaryService.evaluate_metrics(db, deployment.id)
        
        cand_metrics = metrics.get("candidate", {})
        base_metrics = metrics.get("baseline", {})
        
        print(f"  Evaluated database metrics:")
        print(f"    - Baseline: Total: {base_metrics.get('total_interactions')} | thumbs_down rate: {base_metrics.get('thumbs_down_rate'):.2%}")
        print(f"    - Candidate: Total: {cand_metrics.get('total_interactions')} | thumbs_down rate: {cand_metrics.get('thumbs_down_rate'):.2%}")
        
        # Promote rollout progressively
        print(f"  Advancing rollout...")
        deployment = CanaryService.check_and_advance(db, deployment.id)
        print(f"  => Transitioned to State: {deployment.deployment_state} | Rollout: {deployment.rollout_percentage}%\n")
        db.commit()

    # Verify final database persistence and active versions
    db.refresh(v1)
    db.refresh(v2)
    print("="*70)
    print("      FINAL DATABASE STATE VERIFICATION")
    print("="*70)
    print(f"Deployment state:          {deployment.deployment_state}")
    print(f"Deployment percentage:     {deployment.rollout_percentage}%")
    print(f"Prompt v1.0 (baseline) status: {v1.status}")
    print(f"Prompt v1.1-candidate status:  {v2.status}")
    
    assert v2.status == "active"
    assert v1.status == "archived"
    print("\n[+] Verification SUCCESS: Candidate promoted to active with zero rollback.")
    print("="*70)

    db.close()
    # Clean up database
    Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    run_verification()
