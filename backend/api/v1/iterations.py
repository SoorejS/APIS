from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from backend.db.database import get_db
from backend.models.models import IterationJob, QualityPattern
from backend.schemas.admin_schemas import IterationJobOut, QualityPatternOut
from backend.services.iteration_workflow import IterationWorkflow
from backend.services.signal_engine import SignalEngine

router = APIRouter()

@router.post("/namespaces/{namespace_id}/iterate", response_model=IterationJobOut, status_code=status.HTTP_200_OK)
async def trigger_namespace_iteration(namespace_id: UUID, db: Session = Depends(get_db)):
    """
    Directly trigger the full adaptive iteration job for a namespace.
    Performs signal aggregation, policy evaluation, LLM optimization, diff generation, and candidate persistence.
    """
    try:
        job = await IterationWorkflow.run_iteration_flow(db, namespace_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ShouldIterate() gating policy evaluated to False (insufficient signal or within cooldown)."
            )
        return job
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/namespaces/{namespace_id}/iterations", response_model=List[IterationJobOut])
def list_namespace_iterations(namespace_id: UUID, db: Session = Depends(get_db)):
    """
    List all iteration jobs for a specific namespace.
    """
    jobs = db.query(IterationJob).filter(IterationJob.namespace_id == namespace_id).order_by(IterationJob.created_at.desc()).all()
    return jobs

@router.get("/namespaces/{namespace_id}/patterns", response_model=List[QualityPatternOut])
def list_namespace_quality_patterns(namespace_id: UUID, db: Session = Depends(get_db)):
    """
    List detected quality patterns for a namespace.
    Triggers a fresh signal aggregation run first.
    """
    # Trigger a fresh run of pattern detection first to ensure patterns table is updated
    SignalEngine.aggregate_and_detect(db, namespace_id)
    
    patterns = db.query(QualityPattern).filter(
        QualityPattern.namespace_id == namespace_id,
        QualityPattern.status == "active"
    ).all()
    return patterns
