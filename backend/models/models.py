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



