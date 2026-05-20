from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.models import PromptNamespace, PromptVersion, Interaction
from backend.schemas.schemas import RuntimeGenerateRequest, RuntimeGenerateResponse
from backend.services.compiler import PromptCompilerService
from backend.providers.registry import registry
from backend.services.classifier import QueryClassifier
import time

router = APIRouter()

@router.post("/generate", response_model=RuntimeGenerateResponse)
async def generate_runtime(request: RuntimeGenerateRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    # 1. Fetch Namespace
    namespace = db.query(PromptNamespace).filter(PromptNamespace.name == request.namespace).first()
    if not namespace:
        # Auto-create for Week 1 ease of testing
        namespace = PromptNamespace(
            name=request.namespace,
            constraints={"must_preserve": ["Helpful tone"], "cannot_modify": []}
        )
        db.add(namespace)
        db.commit()
        db.refresh(namespace)
        
    # 2. Fetch Active Prompt Version
    active_version = db.query(PromptVersion).filter(
        PromptVersion.namespace_id == namespace.id,
        PromptVersion.status == 'active'
    ).first()
    
    if not active_version:
        # Auto-create v1 for Week 1 ease of testing
        active_version = PromptVersion(
            namespace_id=namespace.id,
            version_string="v1.0",
            content="You are a helpful AI assistant.",
            status="active"
        )
        db.add(active_version)
        db.commit()
        db.refresh(active_version)
        
    selected_version = active_version
    # Check if there is an active canary deployment
    from backend.services.canary import CanaryService
    deployment = CanaryService.get_active_deployment(db, namespace.id)
    if deployment and CanaryService.should_route_to_canary(deployment):
        selected_version = db.query(PromptVersion).filter(PromptVersion.id == deployment.prompt_version_id).first() or active_version

    # 3. Compile Effective Prompt
    effective_prompt = PromptCompilerService.compile_effective_prompt(
        namespace=namespace,
        active_version=selected_version,
        runtime_context=request.context_variables,
        user_query=request.query
    )
    
    # ── LOG COMPILED PROMPT (Requirement 2) ──
    print("\n" + "="*50)
    print("APIS PROMPT COMPILER: EFFECTIVE PROMPT")
    print("="*50)
    print(effective_prompt)
    print("="*50 + "\n")
    
    # 4. Call LLM Provider with optional fallback support
    policy = namespace.iteration_policy or {}
    provider_name = policy.get("provider", "gemini")
    fallback_name = policy.get("fallback_provider", "gemini")
    
    response_text = await registry.generate_with_fallback(
        provider_name=provider_name,
        prompt=effective_prompt,
        fallback_name=fallback_name
    )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # ── CLASSIFY USER QUERY ──
    query_category = QueryClassifier.classify(request.query)
    
    # 5. Log Interaction
    interaction = Interaction(
        namespace_id=namespace.id,
        prompt_version_id=selected_version.id,
        session_id=request.session_id,
        user_query=request.query,
        ai_response=response_text,
        latency_ms=latency_ms,
        provider=provider_name,
        query_category=query_category
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    # 6. Return
    return RuntimeGenerateResponse(
        interaction_id=interaction.id,
        response_text=response_text,
        latency_ms=latency_ms
    )
