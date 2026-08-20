import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def calculate_efficiency_score(
    baseline_latency_ms: int,
    candidate_latency_ms: int,
    baseline_token_cost: float,
    candidate_token_cost: float
) -> float:
    """
    Computes efficiency score: normalized latency reduction + token cost reduction.
    """
    lat_delta = (baseline_latency_ms - candidate_latency_ms) / max(1, baseline_latency_ms)
    cost_delta = (baseline_token_cost - candidate_token_cost) / max(0.0001, baseline_token_cost)
    return round(float(0.5 * lat_delta + 0.5 * cost_delta), 3)


def rank_promoted_candidates(
    candidates: List[Dict[str, Any]],
    baseline_benchmark_passed: int,
    baseline_holdout_passed: int
) -> List[Dict[str, Any]]:
    """
    Hierarchical Quality-First Ranking Policy:
    1. Primary: Highest Holdout Pass Count Delta
    2. Secondary: Highest Living Benchmark Pass Count Delta
    3. Tertiary: Highest Regression Score
    4. Tie-Breaker: Efficiency Score

    Quality ALWAYS dominates; efficiency is purely a tie-breaker.
    """
    def ranking_key(c: Dict[str, Any]):
        holdout_delta = (c.get("holdout_passed") or 0) - baseline_holdout_passed
        benchmark_delta = (c.get("benchmark_passed") or 0) - baseline_benchmark_passed
        regr_score = c.get("regression_score", 0.0)
        eff_score = c.get("efficiency_score", 0.0)

        # Lexicographical sort tuple: (Holdout Δ, Benchmark Δ, Regr, Efficiency)
        return (holdout_delta, benchmark_delta, regr_score, eff_score)

    # Sort descending by key
    sorted_candidates = sorted(candidates, key=ranking_key, reverse=True)

    # Assign transparent ranking scores
    for rank, c in enumerate(sorted_candidates, 1):
        holdout_delta = (c.get("holdout_passed") or 0) - baseline_holdout_passed
        benchmark_delta = (c.get("benchmark_passed") or 0) - baseline_benchmark_passed
        c["ranking_score"] = round(float(holdout_delta * 10.0 + benchmark_delta * 5.0 + c.get("efficiency_score", 0.0)), 2)

    return sorted_candidates
