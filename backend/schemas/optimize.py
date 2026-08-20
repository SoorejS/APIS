from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ── Candidate Configuration Schemas ─────────────────────────────────────────

class CandidateConfigurationOut(BaseModel):
    id: UUID
    experiment_id: UUID
    parent_configuration_id: UUID
    prompt_content: str
    hypothesis: str
    target_failure_patterns: Optional[List[str]] = []
    proposed_change: str
    expected_effect: str
    potential_risk: str
    status: str  # candidate, evaluating_stage_1, evaluating_stage_2, promoted, rejected, failed
    benchmark_passed: int = 0
    benchmark_total: int = 0
    benchmark_score: float = 0.0
    regression_score: float = 0.0
    edge_case_score: float = 0.0
    hard_negative_score: float = 0.0
    holdout_passed: Optional[int] = None
    holdout_total: Optional[int] = None
    holdout_score: Optional[float] = None
    baseline_latency_ms: int = 250
    candidate_latency_ms: int = 250
    baseline_token_cost: float = 0.001
    candidate_token_cost: float = 0.001
    efficiency_score: float = 0.0
    ranking_score: float = 0.0
    rejection_stage: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Optimization Experiment Schemas ─────────────────────────────────────────

class OptimizationExperimentCreate(BaseModel):
    namespace_id: UUID
    parent_configuration_id: UUID
    benchmark_suite_id: UUID
    holdout_version: Optional[str] = "holdout_v1"
    candidate_count: int = Field(default=3, ge=1, le=5)
    ranking_policy: str = "hierarchical_quality_first"
    promotion_thresholds: Optional[Dict[str, int]] = {
        "min_benchmark_improvement_count": 1,
        "max_holdout_drop_count": 0,
        "max_hard_neg_drop_count": 0
    }


class OptimizationExperimentOut(BaseModel):
    id: UUID
    namespace_id: UUID
    parent_configuration_id: UUID
    benchmark_suite_id: UUID
    holdout_version: str
    candidate_count: int
    status: str
    ranking_policy: str
    promotion_thresholds: Optional[Dict[str, Any]] = None
    selected_candidate_id: Optional[UUID] = None
    baseline_benchmark_passed: int = 0
    baseline_benchmark_total: int = 0
    baseline_holdout_passed: int = 0
    baseline_holdout_total: int = 0
    best_candidate_score: float = 0.0
    improvement_delta: float = 0.0
    total_cost: float = 0.0
    total_latency_ms: int = 0
    idempotency_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    candidates: Optional[List[CandidateConfigurationOut]] = []

    class Config:
        from_attributes = True


# ── Comparison & Analysis Schemas ──────────────────────────────────────────

class OptimizationComparisonOut(BaseModel):
    experiment_id: UUID
    baseline: Dict[str, Any]
    candidates: List[CandidateConfigurationOut]
    selected_candidate: Optional[CandidateConfigurationOut] = None
    rejection_summary: Dict[str, List[str]]
    decision_rationale: str
