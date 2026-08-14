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
    db.query(DriftAlert).delete()
    db.query(PromptDeployment).delete()
    db.query(FeedbackSignal).delete()
    db.query(Interaction).delete()
    db.execute(PromptVersion.__table__.update().values(parent_version_id=None))
    db.query(PromptVersion).delete()
    db.query(PromptNamespace).delete()
    db.commit()

    print("Generating new demo data...")

    # ── Namespaces ──────────────────────────────────────────────────────────────
    namespaces_data = [
        {
            "name": "billing-agent",
            "desc": "Handles billing inquiries, invoice explanations, and payment disputes",
            "weight": 0.30,   # 30% of all traffic
            "base_latency": 320,
            "base_error_rate": 0.03,
        },
        {
            "name": "coding-copilot",
            "desc": "Code generation, review, and debugging assistant (multi-language)",
            "weight": 0.28,
            "base_latency": 680,
            "base_error_rate": 0.04,
        },
        {
            "name": "research-assistant",
            "desc": "Summarizes scientific papers, synthesizes literature, generates citations",
            "weight": 0.18,
            "base_latency": 890,
            "base_error_rate": 0.02,
        },
        {
            "name": "customer-support",
            "desc": "Tier-1 customer support routing and FAQ resolution",
            "weight": 0.15,
            "base_latency": 210,
            "base_error_rate": 0.05,
        },
        {
            "name": "invoice-extractor",
            "desc": "Structured JSON extraction from PDF invoices and receipts",
            "weight": 0.09,
            "base_latency": 450,
            "base_error_rate": 0.08,
        },
    ]

    now = datetime.utcnow()

    # Total realistic target: ~103,000 interactions across 5 namespaces
    TOTAL_INTERACTIONS = 103_400
    # Spread over 30 days with realistic daily volume (lower on weekends)
    
    PROVIDERS = ["openai", "gemini", "anthropic"]
    PROVIDER_WEIGHTS = [0.62, 0.28, 0.10]

    for nd in namespaces_data:
        ns = PromptNamespace(
            name=nd["name"],
            description=nd["desc"],
            constraints={"must_preserve": ["tone", "language"], "cannot_modify": ["pii_handling"]},
            iteration_policy={"auto_promote": False, "min_sample_size": 500, "confidence_threshold": 0.95},
            created_at=now - timedelta(days=42)
        )
        db.add(ns)
        db.commit()
        db.refresh(ns)

        # ── Prompt versions: realistic 4-generation evolution ──────────────────
        v1 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.0",
            content=f"You are a helpful AI assistant for {nd['name'].replace('-', ' ')}.",
            status="archived",
            created_at=now - timedelta(days=38)
        )
        db.add(v1)
        db.commit()
        db.refresh(v1)

        v1_1 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.1",
            content=f"You are a helpful AI assistant for {nd['name'].replace('-', ' ')}. Be concise and cite sources when available.",
            status="archived",
            parent_version_id=v1.id,
            change_rationale="Reduced verbosity (avg -18% tokens) after 340 thumbs-down signals in first 7 days. P99 latency improved 120ms.",
            diff_summary={"added": ["Be concise.", "cite sources when available."], "removed": [], "modified": []},
            created_at=now - timedelta(days=28)
        )
        db.add(v1_1)
        db.commit()
        db.refresh(v1_1)

        v1_2_cand = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.2-candidate",
            content=f"You are a precision AI assistant for {nd['name'].replace('-', ' ')}. Be concise, cite sources, and verify factual claims before responding.",
            status="candidate",
            parent_version_id=v1_1.id,
            change_rationale="Hallucination rate spiked to 8.4% on day 14 (model update detected). Candidate adds fact-verification constraint. Canary rolled back: +210ms latency regression exceeded 150ms threshold.",
            diff_summary={"added": ["verify factual claims before responding.", "precision"], "removed": [], "modified": ["helpful"]},
            created_at=now - timedelta(days=12)
        )
        db.add(v1_2_cand)
        db.commit()
        db.refresh(v1_2_cand)

        v1_3 = PromptVersion(
            namespace_id=ns.id,
            version_string="v1.3",
            content=f"You are a precision AI assistant for {nd['name'].replace('-', ' ')}. Respond concisely with verified facts. Format output as structured JSON when extracting data. Escalate uncertainty.",
            status="active",
            parent_version_id=v1_2_cand.id,
            change_rationale="Reworked fact-checking prompt to be embedded, not sequential — eliminating the latency regression from v1.2-candidate. Canary promoted after 50% rollout passed all gates: correctness 96.2%, latency within baseline ±8ms.",
            diff_summary={"added": ["Format output as structured JSON when extracting data.", "Escalate uncertainty."], "removed": [], "modified": ["Respond concisely with verified facts."]},
            created_at=now - timedelta(days=3)
        )
        db.add(v1_3)
        db.commit()
        db.refresh(v1_3)

        # ── Deployments ────────────────────────────────────────────────────────
        # v1.1: successful full promotion
        d1 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_1.id,
            rollout_percentage=100,
            deployment_state="active",
            baseline_metrics={"latency_ms": nd["base_latency"] + 120, "thumbs_down_pct": 9.8, "correctness": 0.82},
            current_metrics={"latency_ms": nd["base_latency"], "thumbs_down_pct": 3.1, "correctness": 0.91},
            created_at=now - timedelta(days=28)
        )
        db.add(d1)

        # v1.2-candidate: failed canary (latency regression)
        d2 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_2_cand.id,
            rollout_percentage=10,
            deployment_state="rolled_back",
            baseline_metrics={"latency_ms": nd["base_latency"], "correctness": 0.91, "hallucination_rate": 8.4},
            current_metrics={"latency_ms": nd["base_latency"] + 218, "correctness": 0.89, "hallucination_rate": 6.1},
            rollback_reason=f"P99 latency regression: +210ms exceeded ±150ms safety threshold after 1,240 canary requests. Automated rollback triggered at 03:47 UTC.",
            created_at=now - timedelta(days=12)
        )
        db.add(d2)

        # v1.3: active canary at 25% (different per namespace for visual variety)
        canary_states = {
            "billing-agent":       ("canary_50", 50),
            "coding-copilot":      ("active", 100),
            "research-assistant":  ("canary_25", 25),
            "customer-support":    ("active", 100),
            "invoice-extractor":   ("canary_10", 10),
        }
        state_key, pct = canary_states.get(nd["name"], ("canary_25", 25))
        d3 = PromptDeployment(
            namespace_id=ns.id,
            prompt_version_id=v1_3.id,
            rollout_percentage=pct,
            deployment_state=state_key,
            baseline_metrics={"latency_ms": nd["base_latency"], "correctness": 0.91, "hallucination_rate": 2.8},
            current_metrics={"latency_ms": nd["base_latency"] - random.randint(5, 25), "correctness": 0.962, "hallucination_rate": 1.1},
            created_at=now - timedelta(days=3)
        )
        db.add(d3)
        db.commit()

        # ── Interactions ───────────────────────────────────────────────────────
        # Realistic volume per namespace, spread across 30 days
        ns_interactions = int(TOTAL_INTERACTIONS * nd["weight"])
        versions_pool = [v1, v1_1, v1_3]
        # Weight v1_3 (active) heaviest, v1 oldest gets least
        version_weights = [0.05, 0.20, 0.75]

        print(f"  Seeding {ns_interactions:,} interactions for {nd['name']}...")

        BATCH_SIZE = 200
        interaction_batch = []
        feedback_batch = []

        for i in range(ns_interactions):
            # Realistic time distribution: Gaussian-ish around business hours
            days_ago = random.uniform(0, 30)
            hour_of_day = random.gauss(14, 5)  # Peak at 2pm, std 5h
            hour_of_day = max(0, min(23, hour_of_day))
            interaction_time = now - timedelta(days=days_ago, hours=hour_of_day % 24)

            v = random.choices(versions_pool, weights=version_weights)[0]
            provider = random.choices(PROVIDERS, weights=PROVIDER_WEIGHTS)[0]

            # Latency: base + noise, with occasional spikes
            base_l = nd["base_latency"]
            if random.random() < 0.03:  # 3% chance of spike
                latency = random.randint(base_l * 3, base_l * 6)
            else:
                latency = int(random.gauss(base_l, base_l * 0.15))
                latency = max(80, latency)

            interaction = Interaction(
                namespace_id=ns.id,
                prompt_version_id=v.id,
                session_id=str(uuid.uuid4()),
                user_query=f"[Realistic {nd['name']} query #{i}]",
                ai_response=f"[Realistic {nd['name']} response]",
                latency_ms=latency,
                provider=provider,
                created_at=interaction_time
            )
            interaction_batch.append(interaction)

            # Add and flush in batches for performance
            if len(interaction_batch) >= BATCH_SIZE:
                db.add_all(interaction_batch)
                db.flush()
                # Add feedback for this batch
                for inter in interaction_batch:
                    if random.random() < 0.12:  # 12% feedback rate (realistic)
                        # Error rate affects thumbs_down probability
                        p_thumbs_down = nd["base_error_rate"] * 2.5
                        signal = "thumbs_down" if random.random() < p_thumbs_down else "thumbs_up"
                        fb = FeedbackSignal(
                            interaction_id=inter.id,
                            signal_type=signal,
                            created_at=inter.created_at + timedelta(minutes=random.uniform(0.5, 30))
                        )
                        feedback_batch.append(fb)
                db.add_all(feedback_batch)
                db.commit()
                interaction_batch = []
                feedback_batch = []

        # Flush remaining
        if interaction_batch:
            db.add_all(interaction_batch)
            db.flush()
            for inter in interaction_batch:
                if random.random() < 0.12:
                    p_thumbs_down = nd["base_error_rate"] * 2.5
                    signal = "thumbs_down" if random.random() < p_thumbs_down else "thumbs_up"
                    fb = FeedbackSignal(
                        interaction_id=inter.id,
                        signal_type=signal,
                        created_at=inter.created_at + timedelta(minutes=random.uniform(0.5, 30))
                    )
                    feedback_batch.append(fb)
            db.add_all(feedback_batch)
            db.commit()

        # ── Drift Alerts ───────────────────────────────────────────────────────
        # Create a realistic incident narrative per namespace
        drift_scenarios = [
            # The main incident: hallucination spike (critical, unresolved) - HIGH IMPACT for demo
            {
                "category": "hallucination_rate",
                "drift_type": "Hallucination rate spiked to 8.4% across 2,847 requests — 3.1σ above 30-day baseline of 2.1%. Correlated with upstream model provider update at 02:14 UTC.",
                "severity": "critical",
                "recommendation": "iterate",
                "resolved": False,
                "hours_ago": random.randint(6, 18),
            },
            # A resolved latency spike
            {
                "category": "latency",
                "drift_type": "P99 latency drifted to 1,840ms (+420ms over 6h rolling baseline). Impacted 12% of requests. Traced to token bloat from verbose responses.",
                "severity": "high",
                "recommendation": "rollback",
                "resolved": True,
                "hours_ago": random.randint(24, 48),
            },
            # A low-severity thumbs-down trend (monitoring)
            {
                "category": "thumbs_down_ratio",
                "drift_type": "Gradual degradation detected: thumbs-down ratio increased from 3.1% to 6.8% over 72h. Insufficient for automated action. Monitoring for threshold breach.",
                "severity": "medium",
                "recommendation": "monitor",
                "resolved": False,
                "hours_ago": random.randint(2, 6),
            },
        ]

        for scenario in drift_scenarios:
            alert = DriftAlert(
                namespace_id=ns.id,
                category=scenario["category"],
                drift_type=scenario["drift_type"],
                severity=scenario["severity"],
                recommendation=scenario["recommendation"],
                resolved=scenario["resolved"],
                created_at=now - timedelta(hours=scenario["hours_ago"])
            )
            db.add(alert)

        db.commit()
        print(f"  [ok] {nd['name']} complete.")

    print(f"\n{'='*60}")
    print(f"Demo data seeded successfully.")
    print(f"Total interactions: ~{TOTAL_INTERACTIONS:,}")
    print(f"Namespaces: {len(namespaces_data)}")
    print(f"Drift alerts: {len(namespaces_data) * 3} (mix of critical/resolved/monitoring)")
    print(f"{'='*60}")
    db.close()

if __name__ == "__main__":
    seed_data()
