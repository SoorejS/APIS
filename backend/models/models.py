from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from backend.db.database import Base

class PromptNamespace(Base):
    __tablename__ = "prompt_namespaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    constraints = Column(JSON) # {"must_preserve": [], "cannot_modify": []}
    iteration_policy = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    versions = relationship("PromptVersion", back_populates="namespace")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    version_string = Column(String(50), nullable=False)
    content = Column(Text, nullable=False) # BASE PROMPT
    status = Column(String(50), nullable=False) # 'candidate', 'approved', 'active', 'archived'
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True)
    change_rationale = Column(Text)
    diff_summary = Column(JSON)
    success_metrics = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    namespace = relationship("PromptNamespace", back_populates="versions")

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    session_id = Column(String(255))
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    latency_ms = Column(Integer)
    provider = Column(String(50))
    query_category = Column(String(100), nullable=True, default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    feedback = relationship("FeedbackSignal", back_populates="interaction")

class FeedbackSignal(Base):
    __tablename__ = "feedback_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id"), nullable=False)
    signal_type = Column(String(50), nullable=False)
    weight = Column(Float, default=1.0)
    is_adversarial = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interaction = relationship("Interaction", back_populates="feedback")

class QualityPattern(Base):
    __tablename__ = "quality_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    pattern_type = Column(String(100), nullable=False) # e.g. "high_negative_feedback"
    query_category = Column(String(100), nullable=False) # e.g. "billing"
    signal_type = Column(String(50)) # e.g. "thumbs_down"
    negative_rate = Column(Float, nullable=False)
    signal_count = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String(50), default="active") # "active", "resolved"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IterationJob(Base):
    __tablename__ = "iteration_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False) # current active version
    candidate_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True) # generated candidate version
    status = Column(String(50), nullable=False, default="pending") # "pending", "running", "completed", "failed"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    active_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    candidate_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending") # "pending", "running", "completed", "failed"
    overall_active_score = Column(Float, nullable=True)
    overall_candidate_score = Column(Float, nullable=True)
    category_scores = Column(JSON, nullable=True) # Detailed dict showing scores and deltas per category
    decision = Column(String(50), nullable=True) # "promoted", "rejected"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FailureMemory(Base):
    __tablename__ = "failure_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    failed_pattern = Column(Text, nullable=False)
    attempted_fix = Column(Text, nullable=False)
    evaluation_result = Column(String(50), default="rejected")
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PromptDeployment(Base):
    __tablename__ = "prompt_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    rollout_percentage = Column(Integer, default=0, nullable=False)
    deployment_state = Column(String(50), nullable=False, default="candidate")
    baseline_metrics = Column(JSON, nullable=True)
    current_metrics = Column(JSON, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])
    prompt_version = relationship("PromptVersion", foreign_keys=[prompt_version_id])


class DriftAlert(Base):
    __tablename__ = "drift_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    category = Column(String(100), nullable=False)
    drift_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    recommendation = Column(String(50), nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])


# ── V1.5 Failure Intelligence & Living Evaluation Models ──────────────────

class FailurePattern(Base):
    __tablename__ = "failure_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=True)
    title = Column(String(255), nullable=False)
    diagnosis = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # tool_selection, hallucination, syntax, retrieval, constraint_violation
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    interaction_count = Column(Integer, nullable=False, default=0)
    recurrence_rate = Column(Float, nullable=False, default=0.0)  # interactions_assigned / eligible_interactions
    recurrence_trend = Column(Float, nullable=False, default=0.0)  # WoW velocity change
    cluster_confidence = Column(Float, nullable=False, default=0.0)  # mean(hdbscan_membership_probabilities)
    cluster_cohesion = Column(Float, nullable=False, default=0.0)  # mean(cosine_similarity_to_centroid)
    diagnosis_confidence = Column(Float, nullable=False, default=0.0)  # LLM diagnosis confidence [0, 1]
    exemplar_interaction_ids = Column(JSON, nullable=True)  # List of Interaction IDs
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])
    benchmark_cases = relationship("LivingBenchmarkCase", back_populates="pattern")


class BenchmarkSuite(Base):
    __tablename__ = "benchmark_suites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    case_count = Column(Integer, nullable=False, default=0)
    idempotency_hash = Column(String(128), unique=True, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])
    cases = relationship("LivingBenchmarkCase", back_populates="suite")


class LivingBenchmarkCase(Base):
    __tablename__ = "living_benchmark_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("failure_patterns.id"), nullable=True)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    archetype = Column(String(50), nullable=False)  # regression, edge_case, hard_negative
    input_prompt = Column(Text, nullable=False)
    expected_output_criteria = Column(Text, nullable=False)
    negative_constraint = Column(Text, nullable=True)  # Specifically for hard_negative: what model must NOT do
    assertion_type = Column(String(50), nullable=False, default="semantic_criteria")  # tool_call_match, semantic_criteria, json_schema, exact_match
    source = Column(String(100), default="production_failure_cluster")
    is_synthetic = Column(Boolean, default=True, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_confidence = Column(Float, nullable=False, default=0.0)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    suite = relationship("BenchmarkSuite", back_populates="cases")
    pattern = relationship("FailurePattern", back_populates="benchmark_cases")
    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    idempotency_hash = Column(String(128), index=True, nullable=True)
    status = Column(String(50), nullable=False, default="queued")  # queued, running, completed, failed
    progress = Column(Float, default=0.0, nullable=False)
    eligible_interactions = Column(Integer, default=0, nullable=False)
    embedded_count = Column(Integer, default=0, nullable=False)
    noise_count = Column(Integer, default=0, nullable=False)
    valid_clusters = Column(Integer, default=0, nullable=False)
    tests_generated = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])


# ── V2 Autonomous Configuration Optimization Models ───────────────────────

class ImmutableConstraint(Base):
    __tablename__ = "immutable_constraints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    constraint_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])


class OptimizationExperiment(Base):
    __tablename__ = "optimization_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("prompt_namespaces.id"), nullable=False)
    parent_configuration_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    benchmark_suite_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_suites.id"), nullable=False)
    holdout_version = Column(String(50), default="holdout_v1", nullable=False)
    candidate_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="queued", nullable=False)  # queued, generating_candidates, evaluating_stage_1, evaluating_stage_2, ranking, completed, failed
    ranking_policy = Column(String(50), default="hierarchical_quality_first", nullable=False)
    promotion_thresholds = Column(JSON, nullable=True)  # {"min_benchmark_improvement_count": 1, "max_holdout_drop_count": 0, "max_hard_neg_drop_count": 0}
    selected_candidate_id = Column(UUID(as_uuid=True), nullable=True)
    baseline_benchmark_passed = Column(Integer, default=0, nullable=False)
    baseline_benchmark_total = Column(Integer, default=0, nullable=False)
    baseline_holdout_passed = Column(Integer, default=0, nullable=False)
    baseline_holdout_total = Column(Integer, default=0, nullable=False)
    best_candidate_score = Column(Float, default=0.0, nullable=False)
    improvement_delta = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    total_latency_ms = Column(Integer, default=0, nullable=False)
    idempotency_hash = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    namespace = relationship("PromptNamespace", foreign_keys=[namespace_id])
    benchmark_suite = relationship("BenchmarkSuite", foreign_keys=[benchmark_suite_id])
    candidates = relationship("CandidateConfiguration", back_populates="experiment")


class CandidateConfiguration(Base):
    __tablename__ = "candidate_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("optimization_experiments.id"), nullable=False)
    parent_configuration_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    prompt_content = Column(Text, nullable=False)
    hypothesis = Column(Text, nullable=False)
    target_failure_patterns = Column(JSON, nullable=True)  # Array of Pattern IDs
    proposed_change = Column(Text, nullable=False)
    expected_effect = Column(Text, nullable=False)
    potential_risk = Column(Text, nullable=False)
    status = Column(String(50), default="candidate", nullable=False)  # candidate, evaluating_stage_1, evaluating_stage_2, promoted, rejected, failed
    benchmark_passed = Column(Integer, default=0, nullable=False)
    benchmark_total = Column(Integer, default=0, nullable=False)
    benchmark_score = Column(Float, default=0.0, nullable=False)
    regression_score = Column(Float, default=0.0, nullable=False)
    edge_case_score = Column(Float, default=0.0, nullable=False)
    hard_negative_score = Column(Float, default=0.0, nullable=False)
    holdout_passed = Column(Integer, nullable=True)
    holdout_total = Column(Integer, nullable=True)
    holdout_score = Column(Float, nullable=True)
    baseline_latency_ms = Column(Integer, default=250, nullable=False)
    candidate_latency_ms = Column(Integer, default=250, nullable=False)
    baseline_token_cost = Column(Float, default=0.001, nullable=False)
    candidate_token_cost = Column(Float, default=0.001, nullable=False)
    efficiency_score = Column(Float, default=0.0, nullable=False)
    ranking_score = Column(Float, default=0.0, nullable=False)
    rejection_stage = Column(String(50), nullable=True)  # stage_1_benchmark, stage_2_holdout, constraint_violation
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("OptimizationExperiment", back_populates="candidates")
