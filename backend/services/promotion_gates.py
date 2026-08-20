import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def evaluate_stage_1_benchmark_gate(
    candidate_passed: int,
    candidate_total: int,
    baseline_passed: int,
    baseline_total: int,
    regression_score: float,
    thresholds: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Stage 1 Quality Gate: Living Benchmark Remediation & Anti-Regression Check.
    Count-first rule: candidate_passed - baseline_passed >= min_benchmark_improvement_count
    """
    min_improvement = thresholds.get("min_benchmark_improvement_count", 1)
    pass_delta = candidate_passed - baseline_passed

    if pass_delta < min_improvement:
        return (
            False,
            f"Stage 1 Rejection: Benchmark improvement count ({pass_delta}) is below required threshold ({min_improvement})."
        )

    # Check regression safety on critical patterns
    if regression_score < 50.0 and baseline_passed > 0:
        return (
            False,
            f"Stage 1 Rejection: Candidate caused severe regression on critical failure patterns (regression score: {regression_score}%)."
        )

    return True, "Stage 1 Gate Passed"


def evaluate_stage_2_holdout_gate(
    candidate_holdout_passed: int,
    candidate_holdout_total: int,
    baseline_holdout_passed: int,
    baseline_holdout_total: int,
    candidate_hard_neg_passed: int,
    baseline_hard_neg_passed: int,
    thresholds: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Stage 2 Generalization Gate: Sealed Holdout & Hard-Negative Degradation Check.
    Count-first rule: candidate_passed - baseline_passed >= -max_allowed_drop_count
    """
    max_holdout_drop = thresholds.get("max_holdout_drop_count", 0)
    max_hard_neg_drop = thresholds.get("max_hard_neg_drop_count", 0)

    holdout_drop = baseline_holdout_passed - candidate_holdout_passed
    if holdout_drop > max_holdout_drop:
        return (
            False,
            f"Stage 2 Rejection: Candidate failed holdout generalization gate (dropped {holdout_drop} cases vs baseline, max allowed drop: {max_holdout_drop})."
        )

    hard_neg_drop = baseline_hard_neg_passed - candidate_hard_neg_passed
    if hard_neg_drop > max_hard_neg_drop:
        return (
            False,
            f"Stage 2 Rejection: Candidate violated Hard Negative boundary constraint (dropped {hard_neg_drop} cases vs baseline)."
        )

    return True, "Stage 2 Gate Passed"
