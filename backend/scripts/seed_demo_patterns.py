import uuid
from datetime import datetime, timezone
from backend.db.database import SessionLocal, engine, Base
from backend.models.models import (
    PromptNamespace, FailurePattern, BenchmarkSuite, LivingBenchmarkCase
)

def seed_demo_failure_intelligence():
    """
    Seeds rich demo Failure Patterns and 3-Archetype Living Benchmarks (is_demo=True)
    strictly isolated from production telemetry data.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        ns = db.query(PromptNamespace).first()
        if not ns:
            ns = PromptNamespace(
                id=uuid.uuid4(),
                name="customer_support",
                description="Enterprise e-commerce and support assistant"
            )
            db.add(ns)
            db.commit()
            db.refresh(ns)

        # Check if demo patterns already exist
        existing = db.query(FailurePattern).filter(FailurePattern.is_demo == True).count()
        if existing > 0:
            print(f"Demo failure patterns already seeded ({existing} patterns found).")
            return

        print("Seeding APIS V1.5 Failure Patterns & Living Benchmark Suites...")

        # 1. Create Demo Benchmark Suite v1
        suite = BenchmarkSuite(
            id=uuid.uuid4(),
            namespace_id=ns.id,
            version_number=1,
            case_count=0,
            idempotency_hash="demo_seed_hash_suite_v1",
            is_demo=True
        )
        db.add(suite)
        db.flush()

        # 2. Pattern 1: Multi-order tracking tool selection
        p1 = FailurePattern(
            id=uuid.uuid4(),
            namespace_id=ns.id,
            title="Multi-Order Tracking Tool Selection & Argument Misalignment",
            diagnosis="When users inquire about multiple shipment tracking numbers in a single prompt, the baseline prompt fails to construct composite tool arguments, only executing the query for the first entity and dropping secondary orders.",
            category="tool_selection",
            severity="high",
            interaction_count=417,
            recurrence_rate=0.128,  # 12.8% of namespace failures
            recurrence_trend=0.34,  # +34% WoW change
            cluster_confidence=0.91,  # mean membership probability
            cluster_cohesion=0.88,  # mean cosine similarity
            diagnosis_confidence=0.92,
            exemplar_interaction_ids=["ex_101", "ex_102", "ex_103"],
            is_demo=True
        )
        db.add(p1)
        db.flush()

        # 3 Archetypes for Pattern 1
        c1_reg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p1.id,
            namespace_id=ns.id,
            archetype="regression",
            input_prompt="Where are my two packages for order #8812 and order #9940?",
            expected_output_criteria="Must invoke order_tracking_tool with both order IDs [8812, 9940] simultaneously.",
            negative_constraint=None,
            assertion_type="tool_call_match",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.96,
            is_demo=True
        )
        c1_edge = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p1.id,
            namespace_id=ns.id,
            archetype="edge_case",
            input_prompt="Track order #8812 and order #9940, where #9940 was cancelled and refunded yesterday.",
            expected_output_criteria="Must track order #8812 via tool and clearly explain the refund status for #9940 without making redundant tool calls.",
            negative_constraint=None,
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.91,
            is_demo=True
        )
        c1_hard_neg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p1.id,
            namespace_id=ns.id,
            archetype="hard_negative",
            input_prompt="What is your policy on shipping delays for orders #8812 and #9940?",
            expected_output_criteria="Explain standard compensation and delay policies accurately without triggering live location tracking APIs.",
            negative_constraint="DO NOT invoke order_tracking_tool or query live package location API.",
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.95,
            is_demo=True
        )
        db.add_all([c1_reg, c1_edge, c1_hard_neg])

        # 3. Pattern 2: JSON Code-Block Wrapping Delimiter Drift
        p2 = FailurePattern(
            id=uuid.uuid4(),
            namespace_id=ns.id,
            title="Structured JSON Delimiter Markdown Escaping Drift",
            diagnosis="Under updated provider system behaviors, the model wraps raw JSON structures in markdown ```json code blocks with conversational preamble, causing automated downstream ingestion parsing failures.",
            category="syntax",
            severity="critical",
            interaction_count=329,
            recurrence_rate=0.101,  # 10.1%
            recurrence_trend=0.48,  # +48% WoW
            cluster_confidence=0.95,
            cluster_cohesion=0.92,
            diagnosis_confidence=0.96,
            exemplar_interaction_ids=["ex_201", "ex_202"],
            is_demo=True
        )
        db.add(p2)
        db.flush()

        c2_reg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p2.id,
            namespace_id=ns.id,
            archetype="regression",
            input_prompt="Extract invoice items from text into strict JSON schema {items: [{sku, qty, price}]}.",
            expected_output_criteria="100% valid parseable JSON object without markdown fences, comments, or leading/trailing text.",
            negative_constraint="DO NOT wrap in ```json code fences.",
            assertion_type="json_schema",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.98,
            is_demo=True
        )
        c2_edge = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p2.id,
            namespace_id=ns.id,
            archetype="edge_case",
            input_prompt="Extract invoice data where price has multi-currency symbols and fractional quantities.",
            expected_output_criteria="Sanitizes currency symbols and extracts numeric floats into JSON schema.",
            negative_constraint=None,
            assertion_type="json_schema",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.89,
            is_demo=True
        )
        c2_hard_neg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p2.id,
            namespace_id=ns.id,
            archetype="hard_negative",
            input_prompt="Write a Python script example that demonstrates how to parse JSON.",
            expected_output_criteria="Provides markdown formatted Python code block with commentary, correctly distinguishing coding request from data extraction.",
            negative_constraint="DO NOT output raw data payload; must output instructional python code.",
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.94,
            is_demo=True
        )
        db.add_all([c2_reg, c2_edge, c2_hard_neg])

        # 4. Pattern 3: Discontinued Product Inventory Hallucination
        p3 = FailurePattern(
            id=uuid.uuid4(),
            namespace_id=ns.id,
            title="Discontinued SKU Availability & Price Hallucination",
            diagnosis="When users inquire about legacy product lines without explicit inventory records in context, the model hallucinates active pricing and delivery estimates rather than requesting SKU clarification.",
            category="hallucination",
            severity="high",
            interaction_count=214,
            recurrence_rate=0.065,  # 6.5%
            recurrence_trend=-0.12, # -12% WoW (healing)
            cluster_confidence=0.89,
            cluster_cohesion=0.85,
            diagnosis_confidence=0.90,
            exemplar_interaction_ids=["ex_301", "ex_302"],
            is_demo=True
        )
        db.add(p3)
        db.flush()

        c3_reg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p3.id,
            namespace_id=ns.id,
            archetype="regression",
            input_prompt="Is Model Pro-2021 in stock at the Seattle warehouse for $399?",
            expected_output_criteria="Correctly identifies Model Pro-2021 as discontinued or states inventory is unverified, without confirming $399 purchase.",
            negative_constraint="DO NOT confirm $399 active purchase or guarantee shipment.",
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.93,
            is_demo=True
        )
        c3_edge = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p3.id,
            namespace_id=ns.id,
            archetype="edge_case",
            input_prompt="Compare replacement parts warranty between legacy Model Pro-2021 and current Pro-2026.",
            expected_output_criteria="Distinguishes grandfathered legacy warranty terms from active current lineup coverage.",
            negative_constraint=None,
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.90,
            is_demo=True
        )
        c3_hard_neg = LivingBenchmarkCase(
            suite_id=suite.id,
            pattern_id=p3.id,
            namespace_id=ns.id,
            archetype="hard_negative",
            input_prompt="Tell me the history and development story of the original Pro-2021 release.",
            expected_output_criteria="Provides engaging historical narrative without triggering inventory warning disclaimers.",
            negative_constraint="DO NOT block response with inventory unavailable disclaimers.",
            assertion_type="semantic_criteria",
            source="production_failure_cluster",
            is_synthetic=True,
            is_validated=True,
            validation_confidence=0.96,
            is_demo=True
        )
        db.add_all([c3_reg, c3_edge, c3_hard_neg])

        suite.case_count = 9
        db.commit()
        print("Successfully seeded APIS V1.5 Failure Patterns (3 patterns, 9 benchmark cases with hard negatives).")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_failure_intelligence()
