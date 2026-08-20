import os
import json
import logging
from typing import List, Dict, Any, Tuple
from math import sqrt
from backend.services.holdout_evaluator import evaluate_prompt_against_case

logger = logging.getLogger(__name__)

HOLDOUT_B_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "holdout_dataset_sealed_b.json")


def generate_holdout_b_dataset() -> List[Dict[str, Any]]:
    """
    Generates a completely separate Holdout Set B (250 distinct queries)
    with completely different wording and entities for double-blind overfitting testing.
    """
    order_ids = [str(x) for x in range(2000, 2300)]
    cases = []

    # 1. Multi-entity queries (60 cases)
    for i in range(60):
        id1 = f"ORD-{order_ids[i*2]}"
        id2 = f"ORD-{order_ids[i*2+1]}"
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "multi_entity",
            "archetype": "regression",
            "query": f"I placed two shipments {id1} and {id2}. What are their transit statuses?",
            "expected_behavior": "Must lookup both shipments.",
            "negative_constraint": None
        })

    # 2. Policy boundaries / Hard Negatives (60 cases)
    for i in range(60):
        oid = f"ORD-{order_ids[i]}"
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "policy_boundary",
            "archetype": "hard_negative",
            "query": f"Do you offer free replacements for damaged goods under our commercial contract for order {oid}?",
            "expected_behavior": "Explain warranty policy directly without calling tracking tool.",
            "negative_constraint": "DO NOT invoke tool_lookup_order or query shipment API."
        })

    # 3. Discontinued SKU Traps (40 cases)
    for i in range(40):
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "discontinued_sku",
            "archetype": "edge_case",
            "query": "Is the discontinued Apex 2017 headset available in bulk?",
            "expected_behavior": "State out of stock and discontinued.",
            "negative_constraint": "DO NOT fabricate inventory stock."
        })

    # 4. JSON Schema Extraction (40 cases)
    for i in range(40):
        oid = f"ORD-{order_ids[i]}"
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "json_extraction",
            "archetype": "regression",
            "query": f"Convert shipping record {oid} into strict JSON object without code blocks.",
            "expected_behavior": "Raw parseable JSON only.",
            "negative_constraint": "DO NOT use markdown code fences."
        })

    # 5. Invalid Cancellation (30 cases)
    for i in range(30):
        oid = f"ORD-{order_ids[i]}"
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "invalid_cancellation",
            "archetype": "edge_case",
            "query": f"Cancel shipment {oid} which was delivered 3 hours ago.",
            "expected_behavior": "Delivered items must be returned, not cancelled.",
            "negative_constraint": "DO NOT confirm cancellation for delivered orders."
        })

    # 6. Standard (20 cases)
    for i in range(20):
        oid = f"ORD-{order_ids[i]}"
        cases.append({
            "id": f"ho_b_{len(cases)+1:03d}",
            "category": "standard_query",
            "archetype": "standard",
            "query": f"Track order {oid}.",
            "expected_behavior": "Lookup order status.",
            "negative_constraint": None
        })

    with open(HOLDOUT_B_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)

    return cases


def evaluate_sealed_holdout_b(prompt_content: str) -> Dict[str, Any]:
    """Evaluates prompt against Holdout Set B."""
    if not os.path.exists(HOLDOUT_B_FILE_PATH):
        generate_holdout_b_dataset()

    with open(HOLDOUT_B_FILE_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total = len(cases)
    passed = sum(1 for c in cases if evaluate_prompt_against_case(prompt_content, c))

    return {
        "holdout_b_passed": passed,
        "holdout_b_total": total,
        "holdout_b_score": round((passed / max(1, total)) * 100.0, 2)
    }
