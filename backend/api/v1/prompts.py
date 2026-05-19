from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from backend.db.database import get_db
from backend.models.models import PromptNamespace, PromptVersion
from backend.schemas.admin_schemas import (
    NamespaceCreate, NamespaceOut,
    PromptVersionCreate, PromptVersionOut,
)

router = APIRouter()


# ── Namespace endpoints ────────────────────────────────────────────────────

@router.get("/namespaces", response_model=List[NamespaceOut])
def list_namespaces(db: Session = Depends(get_db)):
    return db.query(PromptNamespace).all()


@router.post("/namespaces", response_model=NamespaceOut, status_code=201)
def create_namespace(payload: NamespaceCreate, db: Session = Depends(get_db)):
    existing = db.query(PromptNamespace).filter(PromptNamespace.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Namespace already exists")
    ns = PromptNamespace(**payload.model_dump())
    db.add(ns)
    db.commit()
    db.refresh(ns)
    return ns


# ── Prompt version endpoints ───────────────────────────────────────────────

@router.get("/namespaces/{namespace_id}/versions", response_model=List[PromptVersionOut])
def list_versions(namespace_id: UUID, db: Session = Depends(get_db)):
    return db.query(PromptVersion).filter(PromptVersion.namespace_id == namespace_id).all()


@router.post("/namespaces/{namespace_id}/versions", response_model=PromptVersionOut, status_code=201)
def create_version(namespace_id: UUID, payload: PromptVersionCreate, db: Session = Depends(get_db)):
    ns = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
    if not ns:
        raise HTTPException(status_code=404, detail="Namespace not found")

    dup = db.query(PromptVersion).filter(
        PromptVersion.namespace_id == namespace_id,
        PromptVersion.version_string == payload.version_string
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="Version string already exists in namespace")

    pv = PromptVersion(
        namespace_id=namespace_id,
        version_string=payload.version_string,
        content=payload.content,
        status="candidate",
        change_rationale=payload.change_rationale,
    )
    db.add(pv)
    db.commit()
    db.refresh(pv)
    return pv


@router.post("/prompts/{version_id}/activate", response_model=PromptVersionOut)
def activate_version(version_id: UUID, db: Session = Depends(get_db)):
    """
    Promotes a candidate/approved prompt to active.
    Atomically archives the previously-active version first.
    """
    candidate = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Version not found")
    if candidate.status not in ("candidate", "approved"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate a version with status '{candidate.status}'"
        )

    # Archive current active
    db.query(PromptVersion).filter(
        PromptVersion.namespace_id == candidate.namespace_id,
        PromptVersion.status == "active"
    ).update({"status": "archived"})

    candidate.status = "active"
    db.commit()
    db.refresh(candidate)
    return candidate
