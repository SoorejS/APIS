import os
import random
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from backend.db.database import Base, get_db
from backend.main import app
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction
)
from backend.providers.registry import registry

# Setup isolated database for verification
VERIFY_DB_URL = "sqlite:///./provider_fallback_verify.db"
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
    print("      APIS MULTI-PROVIDER FAILURE & FALLBACK VERIFICATION")
    print("="*70 + "\n")

    # 1. Create fresh namespace with Provider Policy
    namespace_name = "multi-provider-service"
    namespace = PromptNamespace(
        name=namespace_name,
        constraints={"must_preserve": []},
        iteration_policy={
            "provider": "openai",
            "fallback_provider": "gemini"
        }
    )
    db.add(namespace)
    db.commit()
    db.refresh(namespace)
    print(f"[1] Created namespace '{namespace_name}'")
    print(f"    - Policy: Primary: {namespace.iteration_policy.get('provider')} | Fallback: {namespace.iteration_policy.get('fallback_provider')}")

    # 2. Create active prompt version
    v1 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.0",
        content="You are a translation assistant.",
        status="active"
    )
    db.add(v1)
    db.commit()
    db.refresh(v1)
    print(f"[2] Created baseline version {v1.version_string} and marked ACTIVE")

    # 3. Simulate healthy provider behavior first
    print("\n--- PHASE 1: Healthy OpenAI Execution ---")
    req_data = {
        "namespace": namespace_name,
        "query": "Translate hello to Spanish."
    }
    
    response = client.post("/api/v1/runtime/generate", json=req_data)
    assert response.status_code == 200
    res_json = response.json()
    interaction_id = res_json["interaction_id"]
    
    interaction = db.query(Interaction).filter(Interaction.id == uuid.UUID(interaction_id)).first()
    print(f"  [+] Request Successful. Latency: {res_json['latency_ms']}ms")
    print(f"  [+] Response Text: {res_json['response_text']}")
    print(f"  [+] Selected Provider recorded in DB: {interaction.provider}")
    assert interaction.provider == "openai"

    # 4. Inject provider failure: OpenAI rate limit (HTTP 429)
    print("\n--- PHASE 2: OpenAI Failure Injection ---")
    print("  [!] Patching OpenAIProvider to simulate API Rate Limit (429)...")
    
    with patch("backend.providers.openai.OpenAIProvider.generate", side_effect=Exception("OpenAI API Error: Rate limit exceeded (status: 429)")):
        print("  [!] Routing query through /generate API while OpenAI is offline...")
        
        fallback_req = {
            "namespace": namespace_name,
            "query": "Translate goodbye to Spanish."
        }
        
        fallback_res = client.post("/api/v1/runtime/generate", json=fallback_req)
        assert fallback_res.status_code == 200
        fallback_json = fallback_res.json()
        
        print(f"  [+] Request completed successfully (NO runtime crash!). Latency: {fallback_json['latency_ms']}ms")
        print(f"  [+] Response Text: {fallback_json['response_text']}")
        
        # Verify fallback response is from Gemini
        assert "[MOCK Gemini]" in fallback_json["response_text"]
        print("  [+] Verified response content contains Gemini output structure.")

    print("\n" + "="*70)
    print("      VERIFICATION SUCCESS: FAILOVER TO GEMINI COMPLETED")
    print("="*70)

    db.close()
    # Clean up database
    Base.metadata.drop_all(bind=engine_v)

if __name__ == "__main__":
    run_verification()
