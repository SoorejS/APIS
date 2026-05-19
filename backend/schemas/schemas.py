from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID


class RuntimeGenerateRequest(BaseModel):
    namespace: str
    query: str
    session_id: Optional[str] = None
    context_variables: Optional[Dict[str, Any]] = None


class RuntimeGenerateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    interaction_id: UUID
    response_text: str
    latency_ms: int


class FeedbackSubmitRequest(BaseModel):
    interaction_id: UUID
    signal_type: str


class FeedbackSubmitResponse(BaseModel):
    status: str
    signal_id: UUID
