from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID


# ── Namespace ──────────────────────────────────────────────────────────────

class NamespaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    constraints: Optional[dict] = None
    iteration_policy: Optional[dict] = None


class NamespaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str]
    constraints: Optional[dict]
    iteration_policy: Optional[dict]


# ── Prompt Versions ────────────────────────────────────────────────────────

class PromptVersionCreate(BaseModel):
    version_string: str
    content: str
    change_rationale: Optional[str] = None


class PromptVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    version_string: str
    content: str
    status: str
    change_rationale: Optional[str]
    diff_summary: Optional[dict]


# ── Quality Pattern ──────────────────────────────────────────────────────────

class QualityPatternOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    namespace_id: UUID
    prompt_version_id: UUID
    pattern_type: str
    query_category: str
    signal_type: Optional[str]
    negative_rate: float
    signal_count: int
    confidence: float
    status: str


# ── Iteration Job ────────────────────────────────────────────────────────────

class IterationJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    namespace_id: UUID
    prompt_version_id: UUID
    candidate_version_id: Optional[UUID]
    status: str
    error_message: Optional[str]

