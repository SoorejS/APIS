import os
import sys
import uuid
import random
from datetime import datetime, timedelta

# Add parent dir to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.db.database import SessionLocal, Base, engine
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction, FeedbackSignal,
    PromptDeployment, DriftAlert
)

def seed_data():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Clearing existing data...")
    # 1. Clean up existing demo data
    db.query(DriftAlert).delete()
    db.query(PromptDeployment).delete()
    db.query(FeedbackSignal).delete()
    db.query(Interaction).delete()
    # Need to update parent_version_id to null to avoid constraint issues before deleting versions
    db.execute(PromptVersion.__table__.update().values(parent_version_id=None))
    db.query(PromptVersion).delete()
    db.query(PromptNamespace).delete()
    
    db.commit()
    print("Generating new demo data...")
    
    namespaces_data = [
        {"name": "billing-agent", "desc": "Handles billing inquiries and invoice explanations"},
        {"name": "coding-copilot", "desc": "Code generation and review assistant"},
        {"name": "research-assistant", "desc": "Summarizes papers and synthesizes facts"},
        {"name": "customer-support", "desc": "General L1 customer support agent"},
        {"name": "invoice-extractor", "desc": "Extracts structured JSON from PDF invoices"}
    ]
    
    now = datetime.utcnow()
    
    for nd in namespaces_data:
        ns = PromptNamespace(
            name=nd["name"],
            description=nd["desc"],
            constraints={"must_preserve": [], "cannot_modify": []},
            iteration_policy={"auto_promote": False},
            created_at=now - timedelta(days=40)
        )
        db.add(ns)
        db.commit()
        db.refresh(ns)
        
        # Create versions
        v1 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.0",
            content="You are a helpful assistant.",
            status="archived",
            created_at=now - timedelta(days=35)
        )
        db.add(v1)
        db.commit()
        db.refresh(v1)
        
        v1_1 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.1",
            content="You are a helpful assistant. Keep it concise.",
            status="archived",
            parent_version_id=v1.id,
            change_rationale="Reduced verbosity after repeated negative feedback",
            diff_summary={"added": ["Keep it concise."], "removed": [], "modified": []},
            created_at=now - timedelta(days=20)
        )
        db.add(v1_1)
        db.commit()
        db.refresh(v1_1)
        
        v1_2_cand = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.2-candidate",
            content="You are a helpful assistant. Keep it concise. Verify facts.",
            status="candidate",
            parent_version_id=v1_1.id,
            change_rationale="Added factual consistency constraints after hallucination spike",
            diff_summary={"added": ["Verify facts."], "removed": [], "modified": []},
            created_at=now - timedelta(days=5)
        )
        db.add(v1_2_cand)
        db.commit()
        db.refresh(v1_2_cand)
        
        v1_3 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.3",
            content="You are a helpful assistant. Keep it very concise. Verify facts carefully.",
            status="active",
            parent_version_id=v1_2_cand.id,
            change_rationale="Optimized token usage and strict formatting rules",
            diff_summary={"added": ["very", "carefully"], "removed": [], "modified": ["Keep it concise.", "Verify facts."]},
            created_at=now - timedelta(days=1)
        )
        db.add(v1_3)
        db.commit()
        db.refresh(v1_3)
        
        # Deployments
        # A successful promotion (v1.1)
        d1 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_1.id,
            rollout_percentage=100,
            deployment_state="active",
            baseline_metrics={"latency_ms": 250, "thumbs_down": 4.5},
            current_metrics={"latency_ms": 240, "thumbs_down": 2.1},
            created_at=now - timedelta(days=20)
        )
        db.add(d1)
        
        # A failed canary (v1.2-cand)
        d2 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_2_cand.id,
            rollout_percentage=10,
            deployment_state="rolled_back",
            baseline_metrics={"latency_ms": 240, "correctness": 95.0},
            current_metrics={"latency_ms": 450, "correctness": 92.0},
            rollback_reason="Latency regression exceeded threshold (+210ms)",
            created_at=now - timedelta(days=5)
        )
        db.add(d2)
        
        # Active canary or active
        state = random.choice(["canary_25", "canary_50", "active"])
        pct = {"canary_25": 25, "canary_50": 50, "active": 100}[state]
        d3 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_3.id,
            rollout_percentage=pct,
            deployment_state=state,
            baseline_metrics={"token_cost": 1.2, "hallucination": 3.1},
            current_metrics={"token_cost": 0.9, "hallucination": 2.8},
            created_at=now - timedelta(days=1)
        )
        db.add(d3)
        
        # Generate Interactions
        versions = [v1, v1_1, v1_3]
        num_interactions = random.randint(200, 300)
        for _ in range(num_interactions):
            interaction_time = now - timedelta(days=random.uniform(0, 30))
            v = random.choice(versions)
            latency = random.randint(200, 800)
            provider = random.choices(["openai", "gemini", "anthropic"], weights=[75, 20, 5])[0]
            
            interaction = Interaction(
                namespace_id=ns.id,
                prompt_version_id=v.id,
                session_id=str(uuid.uuid4()),
                user_query="Sample realistic query based on domain...",
                ai_response="Sample realistic response...",
                latency_ms=latency,
                provider=provider,
                created_at=interaction_time
            )
            db.add(interaction)
            db.flush() # Need ID for feedback
            
            # Feedback
            if random.random() < 0.15: # 15% get feedback
                signal = "thumbs_down" if random.random() < 0.3 else "thumbs_up"
                fb = FeedbackSignal(
                    interaction_id=interaction.id,
                    signal_type=signal,
                    created_at=interaction_time + timedelta(minutes=random.uniform(1, 10))
                )
                db.add(fb)
                
        # Drift Alerts
        categories = ["latency", "hallucination_rate", "thumbs_down_ratio", "verbosity"]
        metrics_desc = {
            "latency": "P99 latency drifted +45ms over 24h",
            "hallucination_rate": "Spiked to 8.4% across 1000 requests",
            "thumbs_down_ratio": "Gradual degradation: 3% to 9% in 3 days",
            "verbosity": "Average token output increased by 15%"
        }
        for _ in range(random.randint(0, 3)):
            cat = random.choice(categories)
            sev = random.choice(["low", "medium", "high", "critical"])
            rec = random.choice(["human_review", "rollback", "iterate", "monitor"])
            
            # Make sure critical alerts are likely unresolved
            resolved = False if sev in ["critical", "high"] else random.choice([True, False])
            
            alert = DriftAlert(
                namespace_id=ns.id,
                category=cat,
                drift_type=metrics_desc[cat],
                severity=sev,
                recommendation=rec,
                resolved=resolved,
                created_at=now - timedelta(hours=random.randint(1, 72))
            )
            db.add(alert)
            
        db.commit()
        
    print("Demo data seeded successfully.")
    db.close()

if __name__ == "__main__":
    seed_data()
