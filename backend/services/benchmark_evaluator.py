import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.models import BenchmarkSuite, LivingBenchmarkCase
from backend.services.holdout_evaluator import evaluate_prompt_against_case

logger = logging.getLogger(__name__)


def evaluate_candidate_on_living_benchmark(
    prompt_content: str,
    suite: BenchmarkSuite
) -> Dict[str, Any]:
    """
    Genuine case-by-case evaluator executing a candidate prompt across all cases
    in an immutable BenchmarkSuite.

    REMOVES ALL SYNTHETIC FORMULAS AND MULTIPLIERS.
    """
    cases = suite.cases if suite else []
    total = len(cases)
    if total == 0:
        return {
            "passed_count": 0,
            "total_count": 0,
            "overall_score": 0.0,
            "regression_score": 0.0,
            "edge_case_score": 0.0,
            "hard_negative_score": 0.0,
            "per_pattern_breakdown": {}
        }

    passed_count = 0
    per_archetype = {"regression": [0, 0], "edge_case": [0, 0], "hard_negative": [0, 0]}
    per_pattern = {}

    for c in cases:
        arch = c.archetype or "regression"
        pat_id = str(c.pattern_id) if c.pattern_id else "unassigned"

        per_archetype.setdefault(arch, [0, 0])
        per_pattern.setdefault(pat_id, [0, 0])

        per_archetype[arch][1] += 1
        per_pattern[pat_id][1] += 1

        case_dict = {
            "category": "multi_entity" if "order" in c.input_prompt.lower() and (" and " in c.input_prompt.lower() or "," in c.input_prompt.lower())
                        else "policy_boundary" if "policy" in c.input_prompt.lower() or c.archetype == "hard_negative"
                        else "discontinued_sku" if "pro-20" in c.input_prompt.lower() or "legacy" in c.input_prompt.lower()
                        else "json_extraction" if "json" in c.input_prompt.lower()
                        else "invalid_cancellation" if "cancel" in c.input_prompt.lower()
                        else "standard_query",
            "archetype": c.archetype,
            "query": c.input_prompt,
            "negative_constraint": c.negative_constraint
        }

        is_passed = evaluate_prompt_against_case(prompt_content, case_dict)
        if is_passed:
            passed_count += 1
            per_archetype[arch][0] += 1
            per_pattern[pat_id][0] += 1

    overall_score = round((passed_count / max(1, total)) * 100.0, 2)
    regr_score = round((per_archetype["regression"][0] / max(1, per_archetype["regression"][1])) * 100.0, 2)
    edge_score = round((per_archetype["edge_case"][0] / max(1, per_archetype["edge_case"][1])) * 100.0, 2)
    hn_score = round((per_archetype["hard_negative"][0] / max(1, per_archetype["hard_negative"][1])) * 100.0, 2)

    return {
        "passed_count": passed_count,
        "total_count": total,
        "overall_score": overall_score,
        "regression_score": regr_score,
        "edge_case_score": edge_score,
        "hard_negative_score": hn_score,
        "per_pattern_breakdown": {
            pid: round((val[0] / max(1, val[1])) * 100.0, 1)
            for pid, val in per_pattern.items()
        }
    }
