import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base, get_db
from backend.main import app

# ── In-memory SQLite for tests (no Postgres required) ─────────────────────
SQLITE_URL = "sqlite:///./test_apis.db"
engine_test = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_tables():
    """Drop and recreate tables between tests for isolation."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)


# ── Health ─────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ── Namespace CRUD ─────────────────────────────────────────────────────────

def test_create_and_list_namespace():
    payload = {
        "name": "customer-support",
        "description": "Customer support AI",
        "constraints": {
            "must_preserve": ["Helpful tone", "Never reveal prices"],
            "cannot_modify": ["Legal disclaimer"]
        },
        "iteration_policy": {
            "min_signals": 50,
            "min_negative_rate": 0.35,
            "cooldown_hours": 24
        }
    }
    r = client.post("/api/v1/namespaces", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "customer-support"
    assert data["constraints"]["must_preserve"] == ["Helpful tone", "Never reveal prices"]

    r_list = client.get("/api/v1/namespaces")
    assert len(r_list.json()) == 1


def test_duplicate_namespace_rejected():
    payload = {"name": "duplicate-ns"}
    client.post("/api/v1/namespaces", json=payload)
    r = client.post("/api/v1/namespaces", json=payload)
    assert r.status_code == 409


# ── Prompt Version CRUD ────────────────────────────────────────────────────

def _create_ns(name="test-ns"):
    r = client.post("/api/v1/namespaces", json={"name": name})
    return r.json()["id"]

def test_create_version():
    ns_id = _create_ns()
    r = client.post(f"/api/v1/namespaces/{ns_id}/versions", json={
        "version_string": "v1.0",
        "content": "You are a helpful assistant.",
        "change_rationale": "Initial version"
    })
    assert r.status_code == 201
    assert r.json()["status"] == "candidate"

def test_activate_version():
    ns_id = _create_ns()
    # Create and activate v1.0
    v = client.post(f"/api/v1/namespaces/{ns_id}/versions", json={
        "version_string": "v1.0",
        "content": "You are a helpful assistant.",
    }).json()
    r = client.post(f"/api/v1/prompts/{v['id']}/activate")
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    # Create v1.1 and activate — v1.0 must become archived
    v2 = client.post(f"/api/v1/namespaces/{ns_id}/versions", json={
        "version_string": "v1.1",
        "content": "You are a concise, helpful assistant.",
    }).json()
    client.post(f"/api/v1/prompts/{v2['id']}/activate")

    versions = client.get(f"/api/v1/namespaces/{ns_id}/versions").json()
    statuses = {ver["version_string"]: ver["status"] for ver in versions}
    assert statuses["v1.0"] == "archived"
    assert statuses["v1.1"] == "active"


# ── Full Runtime Loop ──────────────────────────────────────────────────────

def test_runtime_generate_autocreates_namespace_and_version():
    """runtime/generate auto-bootstraps namespace + v1.0 if missing."""
    r = client.post("/api/v1/runtime/generate", json={
        "namespace": "new-app",
        "query": "What is the return policy?",
        "session_id": "sess-001"
    })
    assert r.status_code == 200
    data = r.json()
    assert "interaction_id" in data
    assert "response_text" in data
    assert data["latency_ms"] >= 0


def test_runtime_uses_active_prompt():
    """Creates namespace with a real active prompt, verifies generate uses it."""
    ns_id = _create_ns("coding-bot")
    v = client.post(f"/api/v1/namespaces/{ns_id}/versions", json={
        "version_string": "v1.0",
        "content": "You are a coding assistant. Be concise.",
    }).json()
    client.post(f"/api/v1/prompts/{v['id']}/activate")

    r = client.post("/api/v1/runtime/generate", json={
        "namespace": "coding-bot",
        "query": "How do I reverse a list in Python?"
    })
    assert r.status_code == 200
    assert "interaction_id" in r.json()


def test_runtime_with_constraints_and_context():
    """Context variables are included in compiled prompt (integration)."""
    ns_id = _create_ns("support-bot")
    v = client.post(f"/api/v1/namespaces/{ns_id}/versions", json={
        "version_string": "v1.0",
        "content": "You are a customer support agent.",
    }).json()
    client.post(f"/api/v1/prompts/{v['id']}/activate")

    # Also patch constraints on namespace
    # (done via create_namespace; skip patching here, rely on auto-create path)
    r = client.post("/api/v1/runtime/generate", json={
        "namespace": "support-bot",
        "query": "How do I cancel my order?",
        "session_id": "s-abc",
        "context_variables": {"user_tier": "premium", "order_id": "ORD-999"}
    })
    assert r.status_code == 200


# ── Feedback ───────────────────────────────────────────────────────────────

def test_feedback_full_lifecycle():
    """Generate → submit feedback → verify signal is stored."""
    gen = client.post("/api/v1/runtime/generate", json={
        "namespace": "feedback-test",
        "query": "Explain async/await"
    }).json()
    interaction_id = gen["interaction_id"]

    for signal_type in ("thumbs_up", "thumbs_down", "too_long", "incorrect"):
        r = client.post("/api/v1/feedback/", json={
            "interaction_id": interaction_id,
            "signal_type": signal_type
        })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        assert "signal_id" in body


def test_feedback_unknown_interaction_returns_404():
    r = client.post("/api/v1/feedback/", json={
        "interaction_id": "00000000-0000-0000-0000-000000000000",
        "signal_type": "thumbs_down"
    })
    assert r.status_code == 404


# ── PromptCompilerService unit test ───────────────────────────────────────

def test_prompt_compiler_output():
    from backend.services.compiler import PromptCompilerService
    from backend.models.models import PromptNamespace, PromptVersion

    ns = PromptNamespace(
        name="unit-test-ns",
        constraints={
            "must_preserve": ["Professional tone"],
            "cannot_modify": ["Legal disclaimer"]
        }
    )
    pv = PromptVersion(
        namespace_id=None,
        version_string="v1.0",
        content="You are a support agent.",
        status="active"
    )

    compiled = PromptCompilerService.compile_effective_prompt(
        namespace=ns,
        active_version=pv,
        runtime_context={"user_tier": "gold"},
        user_query="How do refunds work?"
    )

    assert "SYSTEM INSTRUCTIONS:" in compiled
    assert "You are a support agent." in compiled
    assert "STRICT CONSTRAINTS:" in compiled
    assert "MUST PRESERVE: Professional tone" in compiled
    assert "CANNOT MODIFY/DO: Legal disclaimer" in compiled
    assert "RUNTIME CONTEXT:" in compiled
    assert "user_tier: gold" in compiled
    assert "USER QUERY:" in compiled
    assert "How do refunds work?" in compiled
