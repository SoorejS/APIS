import pytest
import os
import json
import uuid
from sqlalchemy.orm import Session

from backend.experiments.runner import ExperimentRunner
from backend.experiments.metrics import MetricsEngine
from backend.experiments.report_generator import ReportGenerator
from backend.services.failure_memory import FailureMemoryService
from backend.models.models import FailureMemory, PromptNamespace, PromptVersion

@pytest.fixture
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.db.database import Base
    
    SQLITE_URL = "sqlite:///./test_experiments.db"
    engine_test = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_dataset_loading():
    """
    Verify that our 3 benchmark domains load and contain exactly 100 test cases each.
    """
    for domain in ["customer_support", "coding_assistant", "research_assistant"]:
        dataset = ExperimentRunner.load_dataset(domain)
        assert len(dataset) == 100
        for entry in dataset:
            assert "query" in entry
            assert "category" in entry
            assert "difficulty" in entry
            assert "expected_behavior" in entry
            assert "tags" in entry

@pytest.mark.anyio
async def test_metrics_engine():
    """
    Verify that MetricsEngine returns structured, correct, and numeric metrics.
    """
    metrics = await MetricsEngine.evaluate_response(
        query="Explain arrays",
        response="An array is a linear list of elements.",
        expected_behavior="Accurate description of linear list.",
        domain="coding_assistant",
        is_adaptive=True,
        latency_ms=120.5
    )
    
    assert isinstance(metrics["correctness"], float)
    assert isinstance(metrics["helpfulness"], float)
    assert isinstance(metrics["conciseness"], float)
    assert isinstance(metrics["latency_ms"], float)
    assert metrics["latency_ms"] == 120.5
    assert metrics["token_count"] > 0
    assert metrics["failure_rate"] == 0.0

@pytest.mark.anyio
async def test_experiment_runner(db_session: Session):
    """
    Verify ExperimentRunner runs baseline vs adaptive comparison correctly.
    """
    res = await ExperimentRunner.run_experiment(
        db=db_session,
        domain="customer_support",
        sample_size=3
    )
    
    assert res["domain"] == "customer_support"
    assert res["sample_size"] == 3
    assert "baseline" in res
    assert "adaptive" in res
    assert "deltas" in res
    
    # Assert quality scores are numeric
    assert res["baseline"]["helpfulness"] > 0
    assert res["adaptive"]["helpfulness"] > 0
    assert isinstance(res["deltas"]["helpfulness"], float)

def test_report_generation():
    """
    Verify ReportGenerator outputs JSON and GFM Markdown reports properly.
    """
    mock_results = [{
        "domain": "customer_support",
        "sample_size": 5,
        "baseline": {
            "correctness": 0.75, "helpfulness": 0.70, "conciseness": 0.60,
            "relevance": 0.80, "safety": 0.95, "latency_ms": 250.0, "token_count": 45,
            "failure_rate": 0.04, "thumbs_down_rate": 0.35, "hallucination_rate": 0.12, "verbosity": 0.40
        },
        "adaptive": {
            "correctness": 0.88, "helpfulness": 0.90, "conciseness": 0.85,
            "relevance": 0.92, "safety": 1.00, "latency_ms": 180.0, "token_count": 22,
            "failure_rate": 0.0, "thumbs_down_rate": 0.14, "hallucination_rate": 0.02, "verbosity": 0.15
        },
        "deltas": {
            "correctness": 0.13, "helpfulness": 0.20, "conciseness": 0.25,
            "relevance": 0.12, "safety": 0.05, "latency_ms": 70.0, "token_count": 23,
            "failure_rate": 0.04, "thumbs_down_rate": 0.21, "hallucination_rate": 0.10, "verbosity": 0.25
        }
    }]
    
    json_path, md_path = ReportGenerator.generate_reports(mock_results, output_dir="backend/tests")
    
    assert os.path.exists(json_path)
    assert os.path.exists(md_path)
    
    # Verify contents
    with open(json_path, "r") as f:
        data = json.load(f)
        assert data[0]["domain"] == "customer_support"
        
    with open(md_path, "r") as f:
        content = f.read()
        assert "# APIS Experimental Results" in content
        assert "Customer Support" in content
        
    # Clean up test output
    os.remove(json_path)
    os.remove(md_path)

def test_failure_memory_crud(db_session: Session):
    """
    Verify that FailureMemoryService records, queries, and formats failures correctly.
    """
    ns_id = uuid.uuid4()
    
    # Create namespace in DB first
    ns = PromptNamespace(
        id=ns_id,
        name=f"test-fail-ns-{ns_id}",
        constraints={"must_preserve": [], "cannot_modify": []}
    )
    db_session.add(ns)
    db_session.commit()
    
    # Record a failure
    fail_rec = FailureMemoryService.record_failure(
        db=db_session,
        namespace_id=ns_id,
        failed_pattern="coding quality regression",
        attempted_fix="Enforced high conciseness in base prompt",
        reason="coding regressed from 0.90 to 0.84"
    )
    
    assert fail_rec.id is not None
    assert fail_rec.namespace_id == ns_id
    assert fail_rec.failed_pattern == "coding quality regression"
    
    # Fetch failures
    failures = FailureMemoryService.get_failures(db_session, ns_id)
    assert len(failures) == 1
    assert failures[0].reason == "coding regressed from 0.90 to 0.84"
    
    # Verify prompt formatting context
    prompt_context = FailureMemoryService.get_formatted_failures_prompt(db_session, ns_id)
    assert "HISTORICAL FAILURE MEMORY" in prompt_context
    assert "coding quality regression" in prompt_context
    assert "Enforced high conciseness in base prompt" in prompt_context
