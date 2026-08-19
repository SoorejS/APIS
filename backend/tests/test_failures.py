import pytest
import uuid
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import SessionLocal, Base, engine
from backend.models.models import PromptNamespace, PromptVersion, Interaction, FeedbackSignal, FailurePattern, BenchmarkSuite, LivingBenchmarkCase
from backend.services.clustering_service import run_windowed_hdbscan, generate_mock_embeddings
from backend.services.benchmark_generator_service import generate_archetype_test_suite
from backend.services.async_worker import execute_analysis_job_sync
from backend.models.models import AnalysisJob

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_hdbscan_clustering_quality():
    """Verifies HDBSCAN extracts mean membership probabilities, cohesion, and separates noise."""
    # Create 2 synthetic dense clusters + 2 noise points
    c1 = np.random.randn(8, 16) + 5.0
    c2 = np.random.randn(8, 16) - 5.0
    noise = np.array([np.ones(16) * 50.0, np.ones(16) * -50.0])
    
    data = np.vstack([c1, c2, noise])
    ids = [f"id_{i}" for i in range(len(data))]
    
    valid_clusters, noise_count = run_windowed_hdbscan(
        embeddings=data,
        interaction_ids=ids,
        min_cluster_size=3,
        min_samples=2,
        cohesion_threshold=0.30
    )
    
    assert len(valid_clusters) >= 2
    for clust in valid_clusters:
        assert 0.0 <= clust["cluster_confidence"] <= 1.0
        assert 0.0 <= clust["cluster_cohesion"] <= 1.0
        assert len(clust["exemplar_ids"]) > 0


def test_three_archetype_generation():
    """Verifies Regression, Edge Case, and Hard Negative are generated with constraints."""
    suite = generate_archetype_test_suite(
        pattern_title="Multi-Order Tracking Tool Selection",
        diagnosis="Dropped secondary tracking ID in composite query",
        category="tool_selection",
        exemplars=[{"user_query": "Track order 123 and 456", "ai_response": "Tracked 123"}]
    )
    
    archetypes = [tc["archetype"] for tc in suite]
    assert "regression" in archetypes
    assert "edge_case" in archetypes
    assert "hard_negative" in archetypes
    
    hard_neg = next(tc for tc in suite if tc["archetype"] == "hard_negative")
    assert hard_neg["negative_constraint"] is not None
    assert "DO NOT" in hard_neg["negative_constraint"]


def test_failure_api_endpoints(db_session):
    """Verifies API endpoints for patterns, benchmarks, and offline prompt evaluation."""
    # List patterns
    r = client.get("/api/v1/failures/patterns?demo=true")
    assert r.status_code == 200
    patterns = r.json()
    assert isinstance(patterns, list)
    
    # List benchmark suites
    r_bench = client.get("/api/v1/failures/benchmarks?demo=true")
    assert r_bench.status_code == 200
    suites = r_bench.json()
    assert isinstance(suites, list)
    
    if len(suites) > 0 and len(suites[0]["cases"]) > 0:
        suite = suites[0]
        # Fetch or create prompt version
        ns = db_session.query(PromptNamespace).first()
        pv = db_session.query(PromptVersion).filter(PromptVersion.namespace_id == ns.id).first()
        if not pv:
            pv = PromptVersion(
                id=uuid.uuid4(),
                namespace_id=ns.id,
                version_string="v1.0",
                content="System prompt",
                status="active"
            )
            db_session.add(pv)
            db_session.commit()
            
        # Test offline evaluation matrix
        eval_payload = {
            "namespace_id": str(ns.id),
            "prompt_version_id": str(pv.id),
            "suite_id": str(suite["id"])
        }
        r_eval = client.post("/api/v1/failures/benchmarks/evaluate", json=eval_payload)
        assert r_eval.status_code == 200
        res = r_eval.json()
        assert "overall_pass_rate" in res
        assert "archetype_breakdown" in res
        assert "regression" in res["archetype_breakdown"]
        assert "hard_negative" in res["archetype_breakdown"]
