from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from backend.db.database import get_db
from backend.models.models import EvaluationRun
from backend.services.evaluator import EvaluatorService

router = APIRouter()

class EvaluationRequest(BaseModel):
    candidate_version_id: UUID
    simulate_regression: Optional[bool] = False

class EvaluationRunOut(BaseModel):
    id: UUID
    namespace_id: UUID
    active_version_id: UUID
    candidate_version_id: UUID
    status: str
    overall_active_score: Optional[float] = None
    overall_candidate_score: Optional[float] = None
    category_scores: Optional[dict] = None
    decision: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

@router.post("/namespaces/{namespace_id}/evaluations/run", response_model=EvaluationRunOut, status_code=status.HTTP_201_CREATED)
async def trigger_offline_evaluation(
    namespace_id: UUID,
    payload: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an offline prompt evaluation comparing a candidate prompt versus the active prompt.
    Applies strict promotion gating rules: candidates are promoted to ACTIVE only if they improve overall metrics
    and DO NOT regress any single category. Otherwise, the candidate is REJECTED.
    """
    try:
        run = await EvaluatorService.run_offline_evaluation(
            db=db,
            namespace_id=namespace_id,
            candidate_version_id=payload.candidate_version_id,
            simulate_regression=payload.simulate_regression
        )
        return run
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/namespaces/{namespace_id}/evaluations", response_model=List[EvaluationRunOut])
def list_namespace_evaluations(namespace_id: UUID, db: Session = Depends(get_db)):
    """
    List all offline evaluation runs for a namespace.
    """
    runs = db.query(EvaluationRun).filter(
        EvaluationRun.namespace_id == namespace_id
    ).order_by(EvaluationRun.created_at.desc()).all()
    return runs
