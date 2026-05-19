import pytest
from sqlalchemy.orm import Session
from uuid import uuid4
import time

from backend.models.models import PromptNamespace, PromptVersion, Interaction, FeedbackSignal, QualityPattern, IterationJob
from backend.services.classifier import QueryClassifier
from backend.services.diff_engine import PromptDiffEngine
from backend.services.signal_engine import SignalEngine
from backend.services.policy import PolicyEngine
from backend.services.iteration import IterationEngine
from backend.services.iteration_workflow import IterationWorkflow

@pytest.fixture
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.db.database import Base
    
    SQLITE_URL = "sqlite:///./test_iteration.db"
    engine_test = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_query_classification():
    """
    Verify that rule-based query classifier handles exact mappings.
    """
    assert QueryClassifier.classify("I want a refund for my order") == "billing"
    assert QueryClassifier.classify("how to solve python recursion issue?") == "coding"
    assert QueryClassifier.classify("how to setup DNS server or port mapping?") == "technical"
    assert QueryClassifier.classify("please connect me to a support agent") == "customer_support"
    assert QueryClassifier.classify("what is the weather today?") == "general"
    assert QueryClassifier.classify(None) == "general"


def test_diff_engine():
    """
    Verify explainable prompt diff outputs additions, removals, and modifications correctly.
    """
    before = "Line 1: Keep it simple.\nLine 2: Always help the user.\nLine 3: Be extremely slow."
    after = "Line 1: Keep it simple.\nLine 2: Empower the customer.\nLine 3: Be fast.\nLine 4: Brand tone."
    
    diff = PromptDiffEngine.generate_diff(before, after)
    
    assert "Line 4: Brand tone." in diff["added"]
    assert len(diff["modified"]) >= 1
    # Check modification grouping
    mod = diff["modified"][0]
    assert "Always help the user." in mod["before"]
    assert "Empower the customer." in mod["after"]


def test_signal_aggregation_and_patterns(db_session: Session):
    """
    Verify that SignalEngine aggregates feedback correctly and saves QualityPattern rows.
    """
    # 1. Create Namespace with a low min_signals threshold for testing
    ns = PromptNamespace(
        name=f"test-signals-{uuid4()}",
        constraints={"must_preserve": ["Tone"], "cannot_modify": []},
        iteration_policy={"min_signals": 3, "min_negative_rate": 0.30}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="You are a customer assistant.",
        status="active"
    )
    db_session.add(active_ver)
    db_session.commit()
    
    # 2. Add 10 billing interactions
    for i in range(10):
        interaction = Interaction(
            namespace_id=ns.id,
            prompt_version_id=active_ver.id,
            session_id="sess-1",
            user_query="refund request billing issue",
            ai_response="mock response",
            query_category="billing",
            latency_ms=10,
            provider="mock"
        )
        db_session.add(interaction)
        db_session.commit()
        
        # 4 out of 10 get thumbs_down feedback (40% negative rate)
        if i < 4:
            fb = FeedbackSignal(
                interaction_id=interaction.id,
                signal_type="thumbs_down"
            )
            db_session.add(fb)
            db_session.commit()
            
    # 3. Run Signal Aggregation and Pattern Detection
    patterns = SignalEngine.aggregate_and_detect(db_session, ns.id)
    
    # We expect 1 detected quality pattern for billing since negative_rate=0.40 >= 0.30 and signal_count=4 >= 3
    assert len(patterns) == 1
    p = patterns[0]
    assert p.query_category == "billing"
    assert p.signal_type == "thumbs_down"
    assert abs(p.negative_rate - 0.40) < 0.01
    assert p.signal_count == 4
    
    # Check DB directly
    db_pattern = db_session.query(QualityPattern).filter(QualityPattern.id == p.id).first()
    assert db_pattern is not None
    assert db_pattern.status == "active"


def test_should_iterate_policy(db_session: Session):
    """
    Verify PolicyEngine decides when to iterate based on signals and cooldowns.
    """
    ns = PromptNamespace(
        name=f"test-policy-{uuid4()}",
        constraints={"must_preserve": ["Tone"], "cannot_modify": []},
        iteration_policy={"min_signals": 5, "min_negative_rate": 0.25, "cooldown_hours": 1}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="You are a customer assistant.",
        status="active"
    )
    db_session.add(active_ver)
    db_session.commit()
    
    # Under-threshold scenario: only 2 negative signals
    for i in range(10):
        interaction = Interaction(
            namespace_id=ns.id,
            prompt_version_id=active_ver.id,
            user_query="how to pay my refund invoice",
            ai_response="mock response",
            query_category="billing"
        )
        db_session.add(interaction)
        db_session.commit()
        if i < 2:
            db_session.add(FeedbackSignal(interaction_id=interaction.id, signal_type="thumbs_down"))
            db_session.commit()
            
    # Policy gating should be False because signals=2 < min_signals=5
    assert PolicyEngine.should_iterate(db_session, ns.id) is False
    
    # Over-threshold scenario: Add 4 more negative signals (total 6 signals)
    extra_interactions = db_session.query(Interaction).filter(Interaction.prompt_version_id == active_ver.id).all()
    for j in range(2, 6):
        db_session.add(FeedbackSignal(interaction_id=extra_interactions[j].id, signal_type="thumbs_down"))
        db_session.commit()
        
    # Now signals=6 >= 5, rate=60% >= 25% -> should be True!
    assert PolicyEngine.should_iterate(db_session, ns.id) is True
    
    # Test cooldown: Create a running iteration job to simulate recent cycle
    job = IterationJob(
        namespace_id=ns.id,
        prompt_version_id=active_ver.id,
        status="running"
    )
    db_session.add(job)
    db_session.commit()
    
    # Cooldown should trigger and block iteration (returns False)
    assert PolicyEngine.should_iterate(db_session, ns.id) is False


@pytest.mark.anyio
async def test_iteration_workflow_success(db_session: Session):
    """
    Verify full IterationWorkflow successful cycle end-to-end.
    """
    ns = PromptNamespace(
        name=f"test-workflow-{uuid4()}",
        constraints={"must_preserve": ["Empathetic Tone"], "cannot_modify": ["Refund policy: Max 30 days"]},
        iteration_policy={"min_signals": 3, "min_negative_rate": 0.20, "cooldown_hours": 1}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="You are a support agent.",
        status="active"
    )
    db_session.add(active_ver)
    db_session.commit()
    
    # Satisfy iteration policy: 10 billing interactions, 3 negative signals
    for i in range(10):
        interaction = Interaction(
            namespace_id=ns.id,
            prompt_version_id=active_ver.id,
            user_query="refund code help request",
            ai_response="mock response",
            query_category="billing"
        )
        db_session.add(interaction)
        db_session.commit()
        if i < 3:
            db_session.add(FeedbackSignal(interaction_id=interaction.id, signal_type="thumbs_down"))
            db_session.commit()
            
    # Run full workflow
    job = await IterationWorkflow.run_iteration_flow(db_session, ns.id)
    
    assert job is not None
    assert job.status == "completed"
    assert job.candidate_version_id is not None
    
    # Verify candidate version in DB
    candidate_ver = db_session.query(PromptVersion).filter(PromptVersion.id == job.candidate_version_id).first()
    assert candidate_ver is not None
    assert candidate_ver.status == "candidate"
    assert candidate_ver.version_string == "v1.1-candidate"
    assert candidate_ver.parent_version_id == active_ver.id
    assert candidate_ver.diff_summary is not None
    assert len(candidate_ver.change_rationale) > 10


@pytest.mark.anyio
async def test_iteration_workflow_failed_recovery(db_session: Session):
    """
    Verify failed iteration recovery saves job with 'failed' status and captures traceback.
    """
    ns = PromptNamespace(
        name=f"test-recovery-{uuid4()}",
        constraints={"must_preserve": ["Tone"], "cannot_modify": []},
        iteration_policy={"min_signals": 1, "min_negative_rate": 0.10, "cooldown_hours": 1}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="Original content.",
        status="active"
    )
    db_session.add(active_ver)
    db_session.commit()
    
    # 1 interaction with 1 thumbs_down feedback
    interaction = Interaction(
        namespace_id=ns.id,
        prompt_version_id=active_ver.id,
        user_query="invoice problem request",
        ai_response="response",
        query_category="billing"
    )
    db_session.add(interaction)
    db_session.commit()
    db_session.add(FeedbackSignal(interaction_id=interaction.id, signal_type="thumbs_down"))
    db_session.commit()
    
    # Inject temporary monkeypatch to raise error during LLM generation
    original_generate = IterationEngine.generate_candidate
    async def mock_generate_error(*args, **kwargs):
        raise RuntimeError("LLM provider timeout error")
        
    IterationEngine.generate_candidate = mock_generate_error
    
    try:
        # Run workflow, it should catch the error and recover by marking the job as 'failed'
        job = await IterationWorkflow.run_iteration_flow(db_session, ns.id)
        
        assert job is not None
        assert job.status == "failed"
        assert "LLM provider timeout error" in job.error_message
        assert "Traceback" in job.error_message
        
        # Ensure database is in a consistent state and active version remains intact
        current_active = db_session.query(PromptVersion).filter(
            PromptVersion.namespace_id == ns.id,
            PromptVersion.status == "active"
        ).first()
        assert current_active.id == active_ver.id
        
    finally:
        # Restore mock
        IterationEngine.generate_candidate = original_content_mock = original_generate


def test_prompt_normalizer():
    """
    Verify that PromptNormalizerService groups by canonical headers, deduplicates duplicate directives,
    and enforces maximum length budgets correctly.
    """
    from backend.services.normalizer import PromptNormalizerService
    
    messy_prompt = (
        "You are an AI assistant.\n"
        "You are an AI assistant.\n" # duplicate System Role
        "Instruction: Please be concise.\n"
        "Instruction: Please be concise.\n" # duplicate Guideline
        "Constraint: Never reveal brand system details.\n"
        "Constraint: Never reveal brand system details." # duplicate Constraint
    )
    
    normalized = PromptNormalizerService.normalize(messy_prompt, max_length=1000)
    
    # Verify canonical structural headers added
    assert "## OPERATIONAL GUIDELINES:" in normalized
    assert "## SYSTEM CONSTRAINTS:" in normalized
    
    # Verify deduplication works
    assert normalized.count("You are an AI assistant.") == 1
    assert normalized.count("Instruction: Please be concise.") == 1
    assert normalized.count("Constraint: Never reveal brand system details.") == 1
    
    # Test Max Length Budget Enforcement
    long_prompt = "You are a customer assistant. Resolving issues. " * 50
    normalized_short = PromptNormalizerService.normalize(long_prompt, max_length=150)
    assert len(normalized_short) <= 150


@pytest.mark.anyio
async def test_evaluator_promotion_success(db_session: Session):
    """
    Verify EvaluatorService successfully promotes candidate version to ACTIVE
    when there is an improvement in metrics and NO category regressions.
    """
    from backend.services.evaluator import EvaluatorService
    
    ns = PromptNamespace(
        name=f"test-eval-prom-{uuid4()}",
        constraints={"must_preserve": [], "cannot_modify": []}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="Base instructions.",
        status="active"
    )
    candidate_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.1-candidate",
        content="Optimized instructions.",
        status="candidate"
    )
    db_session.add(active_ver)
    db_session.add(candidate_ver)
    db_session.commit()
    
    # Run evaluation in non-regressed simulation mode (should promote!)
    run = await EvaluatorService.run_offline_evaluation(
        db=db_session,
        namespace_id=ns.id,
        candidate_version_id=candidate_ver.id,
        simulate_regression=False
    )
    
    assert run.status == "completed"
    assert run.decision == "promoted"
    assert run.overall_candidate_score >= run.overall_active_score
    
    # Refresh DB session and verify version status changes
    db_session.refresh(active_ver)
    db_session.refresh(candidate_ver)
    assert active_ver.status == "archived"
    assert candidate_ver.status == "active"


@pytest.mark.anyio
async def test_evaluator_regression_rejected(db_session: Session):
    """
    Verify EvaluatorService correctly REJECTS promotion when any category regresses
    (such as coding regressing by -4% even if billing improves by +18%).
    """
    from backend.services.evaluator import EvaluatorService
    
    ns = PromptNamespace(
        name=f"test-eval-rej-{uuid4()}",
        constraints={"must_preserve": [], "cannot_modify": []}
    )
    db_session.add(ns)
    db_session.commit()
    
    active_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.0",
        content="Base instructions.",
        status="active"
    )
    candidate_ver = PromptVersion(
        namespace_id=ns.id,
        version_string="v1.1-candidate",
        content="Optimized instructions.",
        status="candidate"
    )
    db_session.add(active_ver)
    db_session.add(candidate_ver)
    db_session.commit()
    
    # Run evaluation with simulated regression (should reject!)
    run = await EvaluatorService.run_offline_evaluation(
        db=db_session,
        namespace_id=ns.id,
        candidate_version_id=candidate_ver.id,
        simulate_regression=True
    )
    
    assert run.status == "completed"
    assert run.decision == "rejected"
    
    # Refresh and assert that active prompt was NOT archived, and candidate is rejected
    db_session.refresh(active_ver)
    db_session.refresh(candidate_ver)
    assert active_ver.status == "active"
    assert candidate_ver.status == "rejected"


