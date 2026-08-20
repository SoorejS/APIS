import math
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats


def calculate_wilson_confidence_interval(passed: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes Wilson score 95% confidence interval for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf((1 + confidence) / 2)
    p = passed / total
    denom = 1.0 + (z**2 / total)
    center = (p + (z**2 / (2 * total))) / denom
    margin = (z * math.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))) / denom
    return (round(max(0.0, center - margin) * 100.0, 2), round(min(1.0, center + margin) * 100.0, 2))


def calculate_mcnemar_test(
    baseline_results: List[bool],
    candidate_results: List[bool]
) -> Dict[str, Any]:
    """
    Computes McNemar's exact/continuity-corrected test for paired binary classification outcomes:
    b: Baseline passed, Candidate failed (Candidate regressed)
    c: Baseline failed, Candidate passed (Candidate improved)
    """
    assert len(baseline_results) == len(candidate_results), "Paired outcomes must have identical length"
    
    b = sum(1 for b_res, c_res in zip(baseline_results, candidate_results) if b_res and not c_res)
    c = sum(1 for b_res, c_res in zip(baseline_results, candidate_results) if not b_res and c_res)

    # McNemar's Chi-square with Edwards continuity correction
    if (b + c) == 0:
        p_value = 1.0
        chi2 = 0.0
    else:
        chi2 = (abs(b - c) - 1.0)**2 / (b + c)
        p_value = 1.0 - stats.chi2.cdf(chi2, df=1)

    return {
        "candidate_remediations_count": c,
        "candidate_regressions_count": b,
        "chi2_statistic": round(float(chi2), 3),
        "p_value": float(f"{p_value:.4e}"),
        "statistically_significant": bool(p_value < 0.05)
    }


def calculate_paired_bootstrap_ci(
    baseline_results: List[bool],
    candidate_results: List[bool],
    n_bootstraps: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """Computes non-parametric paired bootstrap confidence interval of the percentage point delta."""
    n = len(baseline_results)
    deltas = []
    base_arr = np.array(baseline_results, dtype=float)
    cand_arr = np.array(candidate_results, dtype=float)

    np.random.seed(42)
    for _ in range(n_bootstraps):
        idx = np.random.randint(0, n, size=n)
        d = (cand_arr[idx].mean() - base_arr[idx].mean()) * 100.0
        deltas.append(d)

    alpha = 1.0 - confidence
    lower = float(np.percentile(deltas, 100 * (alpha / 2)))
    upper = float(np.percentile(deltas, 100 * (1 - alpha / 2)))
    return (round(lower, 2), round(upper, 2))
