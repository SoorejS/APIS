import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from unittest.mock import patch

from backend.db.database import Base
from backend.models.models import (
    PromptNamespace, PromptVersion, Interaction, FeedbackSignal,
    PromptDeployment, DriftAlert
)
from backend.services.canary import CanaryService
from backend.providers.registry import registry
from backend.services.drift import DriftDetector

# In-memory SQLite for testing new features
TEST_DB_URL = "sqlite:///./test_features.db"
engine_feat = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_feat)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine_feat)
    Base.metadata.create_all(bind=engine_feat)
    yield
    Base.metadata.drop_all(bind=engine_feat)

@pytest.fixture(autouse=True)
def db():
    connection = engine_feat.connect()
    transaction = connection.begin()
    session = TestingSession(bind=connection)
    
    # Empty all tables before each test
    session.query(DriftAlert).delete()
    session.query(PromptDeployment).delete()
    session.query(FeedbackSignal).delete()
    session.query(Interaction).delete()
    session.query(PromptVersion).delete()
    session.query(PromptNamespace).delete()
    session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# ── CANARY DEPLOYMENT TESTS ───────────────────────────────────────────────────

def test_canary_promotion_flow(db):
    # Setup namespace and versions
    namespace = PromptNamespace(
        name="billing-test",
        constraints={"must_preserve": []},
        iteration_policy={}
    )
    db.add(namespace)
    db.commit()

    v1 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v1.0",
        content="Hello Base",
        status="active"
    )
    v2 = PromptVersion(
        namespace_id=namespace.id,
        version_string="v2.0",
        content="Hello Candidate",
        status="candidate"
    )
    db.add_all([v1, v2])
    db.commit()

    # Create deployment
    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=v2.id,
        rollout_percentage=0,
        deployment_state="candidate"
    )
    db.add(deployment)
    db.commit()

    # Define custom metrics representing positive execution (no regressions)
    good_metrics = {
        "baseline": {"thumbs_down_rate": 0.05, "avg_latency_ms": 120.0, "correctness": 1.0},
        "candidate": {"thumbs_down_rate": 0.02, "avg_latency_ms": 110.0, "correctness": 1.0}
    }

    # 1. Promote: candidate -> canary_10
    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
    assert deployment.deployment_state == "canary_10"
    assert deployment.rollout_percentage == 10

    # 2. Promote: canary_10 -> canary_25
    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
    assert deployment.deployment_state == "canary_25"
    assert deployment.rollout_percentage == 25

    # 3. Promote: canary_25 -> canary_50
    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
    assert deployment.deployment_state == "canary_50"
    assert deployment.rollout_percentage == 50

    # 4. Promote: canary_50 -> active
    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=good_metrics)
    assert deployment.deployment_state == "active"
    assert deployment.rollout_percentage == 100

    # Verify database prompt version changes
    db.refresh(v1)
    db.refresh(v2)
    assert v1.status == "archived"
    assert v2.status == "active"


def test_canary_rollback_on_negative_feedback(db):
    # Setup namespace and versions
    namespace = PromptNamespace(name="refund-test", constraints={}, iteration_policy={})
    db.add(namespace)
    db.commit()

    v1 = PromptVersion(namespace_id=namespace.id, version_string="v1.0", content="Base content", status="active")
    v2 = PromptVersion(namespace_id=namespace.id, version_string="v2.0", content="Cand content", status="candidate")
    db.add_all([v1, v2])
    db.commit()

    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=v2.id,
        rollout_percentage=25,
        deployment_state="canary_25"
    )
    db.add(deployment)
    db.commit()

    # Scenario: Thumbs down rate spikes from 5% in baseline to 25% in candidate
    bad_metrics = {
        "baseline": {"thumbs_down_rate": 0.05, "avg_latency_ms": 100.0, "correctness": 1.0},
        "candidate": {"thumbs_down_rate": 0.25, "avg_latency_ms": 105.0, "correctness": 1.0}
    }

    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=bad_metrics)
    assert deployment.deployment_state == "rolled_back"
    assert deployment.rollout_percentage == 0
    assert "thumbs_down rate increased" in deployment.rollback_reason


def test_canary_rollback_on_latency_spike(db):
    # Setup namespace and versions
    namespace = PromptNamespace(name="speed-test", constraints={}, iteration_policy={})
    db.add(namespace)
    db.commit()

    v1 = PromptVersion(namespace_id=namespace.id, version_string="v1.0", content="Base content", status="active")
    v2 = PromptVersion(namespace_id=namespace.id, version_string="v2.0", content="Cand content", status="candidate")
    db.add_all([v1, v2])
    db.commit()

    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=v2.id,
        rollout_percentage=25,
        deployment_state="canary_25"
    )
    db.add(deployment)
    db.commit()

    # Scenario: Latency increases significantly (100ms baseline vs 350ms candidate)
    slow_metrics = {
        "baseline": {"thumbs_down_rate": 0.05, "avg_latency_ms": 100.0, "correctness": 1.0},
        "candidate": {"thumbs_down_rate": 0.05, "avg_latency_ms": 350.0, "correctness": 1.0}
    }

    deployment = CanaryService.check_and_advance(db, deployment.id, custom_metrics=slow_metrics)
    assert deployment.deployment_state == "rolled_back"
    assert "latency increased significantly" in deployment.rollback_reason


# ── TRAFFIC ROUTING TESTS ─────────────────────────────────────────────────────

def test_traffic_routing_logic(db):
    namespace = PromptNamespace(name="routing-test", constraints={}, iteration_policy={})
    db.add(namespace)
    db.commit()

    deployment = PromptDeployment(
        namespace_id=namespace.id,
        prompt_version_id=namespace.id,  # Dummy ID
        rollout_percentage=25,
        deployment_state="canary_25"
    )

    # 1. 25% Rollout: Mock random values to verify decision bounds
    with patch("random.randint", return_value=15):
        assert CanaryService.should_route_to_canary(deployment) is True

    with patch("random.randint", return_value=50):
        assert CanaryService.should_route_to_canary(deployment) is False


# ── MULTI-PROVIDER & FALLBACK TESTS ───────────────────────────────────────────

@pytest.mark.anyio
async def test_provider_switching_and_fallback():
    # 1. Test standard mock response retrieval
    openai_prov = registry.get_provider("openai")
    res = await openai_prov.generate("What is the refund rule?")
    assert "[MOCK OpenAI]" in res

    claude_prov = registry.get_provider("claude")
    res2 = await claude_prov.generate("Explain variables.")
    assert "[MOCK Claude]" in res2

    ollama_prov = registry.get_provider("ollama")
    res3 = await ollama_prov.generate("Write loop.")
    assert "[MOCK Ollama]" in res3

    # 2. Test fallback functionality
    # Mocking standard Claude provider to raise exception, triggering fallback to Gemini
    with patch("backend.providers.claude.ClaudeProvider.generate", side_effect=Exception("Claude unavailable")):
        response = await registry.generate_with_fallback("claude", "Test prompt", fallback_name="gemini")
        assert "[MOCK Gemini]" in response


# ── DRIFT DETECTION TESTS ─────────────────────────────────────────────────────

def test_drift_detection_thresholds(db):
    # Setup Namespace
    namespace = PromptNamespace(name="drift-namespace", constraints={}, iteration_policy={})
    db.add(namespace)
    db.commit()

    # Add active prompt version
    v = PromptVersion(namespace_id=namespace.id, version_string="v1.0", content="Base", status="active")
    db.add(v)
    db.commit()

    now = datetime.datetime.now(datetime.timezone.utc)

    # Setup historical baseline interactions (e.g. 15 days ago, low negative rate)
    for i in range(10):
        interaction = Interaction(
            namespace_id=namespace.id,
            prompt_version_id=v.id,
            user_query="How to update billing?",
            ai_response="Navigate to settings.",
            latency_ms=100,
            query_category="billing",
            created_at=now - datetime.timedelta(days=15)
        )
        db.add(interaction)
        db.commit()
        # No feedback signals (0% thumbs down baseline)

    # Setup recent degraded interactions (e.g. 2 days ago, high negative rate)
    for i in range(5):
        interaction = Interaction(
            namespace_id=namespace.id,
            prompt_version_id=v.id,
            user_query="Billing issue!",
            ai_response="I cannot help with billing anymore.",
            latency_ms=500,  # Latency drift trigger (500ms vs 100ms)
            query_category="billing",
            created_at=now - datetime.timedelta(days=2)
        )
        db.add(interaction)
        db.commit()

        # Add thumbs_down feedback
        feedback = FeedbackSignal(
            interaction_id=interaction.id,
            signal_type="thumbs_down"
        )
        db.add(feedback)
        db.commit()

    # Trigger drift detection
    alerts = DriftDetector.detect_drift(db, namespace.id)
    assert len(alerts) > 0

    # Inspect generated alert
    alert_types = [a.drift_type for a in alerts]
    assert "thumbs_down" in alert_types
    assert "latency" in alert_types

    alert_td = [a for a in alerts if a.drift_type == "thumbs_down"][0]
    assert alert_td.severity in ["medium", "high", "critical"]
    assert alert_td.recommendation in ["monitor", "iterate", "rollback"]
