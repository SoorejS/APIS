from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.models import Interaction, FeedbackSignal
from backend.schemas.schemas import FeedbackSubmitRequest, FeedbackSubmitResponse

router = APIRouter()

@router.post("/", response_model=FeedbackSubmitResponse)
def submit_feedback(request: FeedbackSubmitRequest, db: Session = Depends(get_db)):
    # 1. Verify Interaction
    interaction = db.query(Interaction).filter(Interaction.id == request.interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
        
    # 2. Store Feedback
    signal = FeedbackSignal(
        interaction_id=interaction.id,
        signal_type=request.signal_type,
        weight=1.0, # Baseline weight
        is_adversarial=False # To be updated by Signal Engine
    )
    
    db.add(signal)
    db.commit()
    db.refresh(signal)
    
    return FeedbackSubmitResponse(
        status="success",
        signal_id=signal.id
    )
