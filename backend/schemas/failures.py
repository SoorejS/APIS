from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ── Failure Pattern Schemas ──────────────────────────────────────────────────

class FailurePatternOut(BaseModel):
    id: UUID
    namespace_id: UUID
    job_id: Optional[UUID] = None
    title: str
    diagnosis: str
    category: str
    severity: str
    interaction_count: int
    recurrence_rate: float
    recurrence_trend: float
    cluster_confidence: float
    cluster_cohesion: float
    diagnosis_confidence: float
    exemplar_interaction_ids: Optional[List[str]] = []
    is_demo: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Living Benchmark Case Schemas ──────────────────────────────────────────

class LivingBenchmarkCaseOut(BaseModel):
    id: UUID
    suite_id: UUID
    pattern_id: Optional[UUID] = None
    namespace_id: UUID
    archetype: str  # regression, edge_case, hard_negative
    input_prompt: str
    expected_output_criteria: str
    negative_constraint: Optional[str] = None
    assertion_type: str
    source: str
    is_synthetic: bool
    is_validated: bool
    validation_confidence: float
    is_demo: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BenchmarkSuiteOut(BaseModel):
    id: UUID
    namespace_id: UUID
    version_number: int
    case_count: int
    idempotency_hash: Optional[str] = None
    is_demo: bool
    created_at: Optional[datetime] = None
    cases: Optional[List[LivingBenchmarkCaseOut]] = []

    class Config:
        from_attributes = True


# ── Analysis Job Schemas ──────────────────────────────────────────────────

class AnalysisJobCreate(BaseModel):
    namespace_id: UUID
    window_days: int = Field(default=14, ge=1, le=90)
    min_failures: int = Field(default=10, ge=3)
    is_demo: bool = False


class AnalysisJobOut(BaseModel):
    id: UUID
    namespace_id: UUID
    status: str
    progress: float
    eligible_interactions: int
    embedded_count: int
    noise_count: int
    valid_clusters: int
    tests_generated: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Evaluation Schemas ────────────────────────────────────────────────────

class BenchmarkEvaluationRequest(BaseModel):
    namespace_id: UUID
    prompt_version_id: UUID
    suite_id: UUID
    model_name: Optional[str] = "gemini-2.5-flash"


class BenchmarkEvaluationCaseResult(BaseModel):
    case_id: UUID
    archetype: str
    passed: bool
    score: float
    actual_output: str
    rationale: str


class BenchmarkEvaluationOut(BaseModel):
    suite_version: int
    prompt_version_id: UUID
    total_cases: int
    passed_cases: int
    overall_pass_rate: float
    archetype_breakdown: Dict[str, Dict[str, Any]]
    case_results: List[BenchmarkEvaluationCaseResult]
