from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.db.database import get_db
from backend.models.models import (
    OptimizationExperiment, CandidateConfiguration, PromptNamespace,
    PromptVersion, BenchmarkSuite
)
from backend.schemas.optimize import (
    OptimizationExperimentCreate, OptimizationExperimentOut,
    CandidateConfigurationOut, OptimizationComparisonOut
)
from backend.services.optimization_worker import execute_optimization_experiment_sync

router = APIRouter()


@router.post("", response_model=OptimizationExperimentOut, status_code=202)
def start_autonomous_optimization(
    payload: OptimizationExperimentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Starts an asynchronous closed-loop autonomous configuration optimization run."""
    namespace = db.query(PromptNamespace).filter(PromptNamespace.id == payload.namespace_id).first()
    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found")

    prompt_version = db.query(PromptVersion).filter(PromptVersion.id == payload.parent_configuration_id).first()
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Parent PromptVersion not found")

    suite = db.query(BenchmarkSuite).filter(BenchmarkSuite.id == payload.benchmark_suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="BenchmarkSuite not found")

    exp = OptimizationExperiment(
        namespace_id=payload.namespace_id,
        parent_configuration_id=payload.parent_configuration_id,
        benchmark_suite_id=payload.benchmark_suite_id,
        holdout_version=payload.holdout_version or "holdout_v1",
        candidate_count=payload.candidate_count,
        ranking_policy=payload.ranking_policy,
        promotion_thresholds=payload.promotion_thresholds,
        status="queued"
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    def run_opt(exp_id: UUID):
        from backend.db.database import SessionLocal
        exp_db = SessionLocal()
        try:
            execute_optimization_experiment_sync(exp_id, exp_db)
        finally:
            exp_db.close()

    background_tasks.add_task(run_opt, exp.id)
    return exp


@router.get("/{experiment_id}", response_model=OptimizationExperimentOut)
def get_optimization_experiment(experiment_id: UUID, db: Session = Depends(get_db)):
    """Retrieves real-time experiment state, lineage, and baseline counts."""
    exp = db.query(OptimizationExperiment).filter(OptimizationExperiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Optimization experiment not found")
    return exp


@router.get("/{experiment_id}/candidates", response_model=List[CandidateConfigurationOut])
def list_experiment_candidates(experiment_id: UUID, db: Session = Depends(get_db)):
    """Lists all candidate configurations with hypotheses, sample counts (X/N), and stage results."""
    candidates = db.query(CandidateConfiguration).filter(
        CandidateConfiguration.experiment_id == experiment_id
    ).order_by(CandidateConfiguration.ranking_score.desc(), CandidateConfiguration.created_at.asc()).all()
    return candidates


@router.get("/{experiment_id}/comparison", response_model=OptimizationComparisonOut)
def get_experiment_comparison(experiment_id: UUID, db: Session = Depends(get_db)):
    """Provides full differential comparison: baseline vs candidates across holdout, benchmark, and regression analysis."""
    exp = db.query(OptimizationExperiment).filter(OptimizationExperiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Optimization experiment not found")

    candidates = db.query(CandidateConfiguration).filter(
        CandidateConfiguration.experiment_id == experiment_id
    ).order_by(CandidateConfiguration.ranking_score.desc()).all()

    selected = next((c for c in candidates if c.status == "promoted"), None)

    rejection_summary = {"stage_1_benchmark": [], "stage_2_holdout": [], "ranking": []}
    for c in candidates:
        if c.rejection_stage and c.rejection_reason:
            rejection_summary.setdefault(c.rejection_stage, []).append(f"Candidate ({c.id.hex[:6]}): {c.rejection_reason}")

    decision_rationale = (
        f"Candidate {selected.id.hex[:6]} successfully passed Stage 1 Living Benchmark Gate (+{round(selected.benchmark_score - exp.baseline_score, 1)}% delta) and Stage 2 Sealed Holdout Gate ({selected.holdout_passed}/{selected.holdout_total} passed), achieving the highest hierarchical rank. Status: READY_FOR_CANARY."
        if selected else "No candidate satisfied multi-objective safety and holdout generalization gates."
    )

    return OptimizationComparisonOut(
        experiment_id=exp.id,
        baseline={
            "score": exp.baseline_score,
            "benchmark_passed": exp.baseline_benchmark_passed,
            "benchmark_total": exp.baseline_benchmark_total,
            "holdout_passed": exp.baseline_holdout_passed,
            "holdout_total": exp.baseline_holdout_total
        },
        candidates=candidates,
        selected_candidate=selected,
        rejection_summary=rejection_summary,
        decision_rationale=decision_rationale
    )


@router.post("/{experiment_id}/promote", response_model=CandidateConfigurationOut)
def manual_promote_candidate(
    experiment_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db)
):
    """Emergency administrative override endpoint to promote a specific candidate to READY_FOR_CANARY."""
    cand = db.query(CandidateConfiguration).filter(
        CandidateConfiguration.id == candidate_id,
        CandidateConfiguration.experiment_id == experiment_id
    ).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    cand.status = "promoted"
    db.commit()
    db.refresh(cand)
    return cand
