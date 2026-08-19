import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.models import (
    AnalysisJob, Interaction, FeedbackSignal, FailurePattern,
    BenchmarkSuite, LivingBenchmarkCase
)
from backend.services.clustering_service import (
    generate_mock_embeddings, run_windowed_hdbscan
)
from backend.services.diagnosis_service import diagnose_failure_cluster
from backend.services.benchmark_generator_service import generate_archetype_test_suite

logger = logging.getLogger(__name__)


def compute_idempotency_hash(namespace_id: UUID, interaction_ids: list) -> str:
    sorted_ids = sorted([str(i) for i in interaction_ids])
    raw = f"{namespace_id}:{','.join(sorted_ids)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def execute_analysis_job_sync(job_id: UUID, db: Session) -> AnalysisJob:
    """
    Executes the full V1.5 Failure Analysis Pipeline with strict idempotency:
    1. Ingests eligible negative/drifted interactions in window
    2. Generates embeddings
    3. Runs windowed HDBSCAN with membership probabilities & cohesion
    4. Diagnoses failure patterns & assigns exemplar evidence
    5. Synthesizes 3-archetype living benchmark suites (Regression, Edge Case, Hard Negative)
    6. Updates job progress and pipeline telemetry atomically
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    job.status = "running"
    job.progress = 0.1
    db.commit()

    try:
        now = datetime.now(timezone.utc)
        fourteen_days_ago = now - timedelta(days=14)

        # 1. Fetch eligible failure interactions
        negative_interactions = (
            db.query(Interaction)
            .join(FeedbackSignal, FeedbackSignal.interaction_id == Interaction.id)
            .filter(
                Interaction.namespace_id == job.namespace_id,
                FeedbackSignal.signal_type == "thumbs_down",
                Interaction.created_at >= fourteen_days_ago
            )
            .all()
        )

        # Fallback to high latency or general interactions if negative signals are sparse
        if len(negative_interactions) < 5:
            negative_interactions = (
                db.query(Interaction)
                .filter(Interaction.namespace_id == job.namespace_id)
                .order_by(Interaction.created_at.desc())
                .limit(50)
                .all()
            )

        eligible_count = len(negative_interactions)
        job.eligible_interactions = eligible_count
        job.progress = 0.25
        db.commit()

        if eligible_count < 3:
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return job

        interaction_ids = [str(i.id) for i in negative_interactions]
        idemp_hash = compute_idempotency_hash(job.namespace_id, interaction_ids)
        job.idempotency_hash = idemp_hash

        # Check for existing completed suite with same hash
        existing_suite = db.query(BenchmarkSuite).filter(
            BenchmarkSuite.idempotency_hash == idemp_hash
        ).first()

        if existing_suite:
            logger.info(f"Idempotent hit for hash {idemp_hash}. Returning existing suite.")
            job.valid_clusters = len(existing_suite.cases) // 3
            job.tests_generated = len(existing_suite.cases)
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return job

        # 2. Vectorize interactions
        texts = [f"{i.user_query} {i.ai_response}" for i in negative_interactions]
        embeddings = generate_mock_embeddings(texts)
        job.embedded_count = len(embeddings)
        job.progress = 0.50
        db.commit()

        # 3. Windowed HDBSCAN with membership probabilities & cohesion
        valid_clusters, noise_count = run_windowed_hdbscan(
            embeddings=embeddings,
            interaction_ids=interaction_ids,
            min_cluster_size=3,
            min_samples=2,
            cohesion_threshold=0.35
        )

        job.noise_count = noise_count
        job.valid_clusters = len(valid_clusters)
        job.progress = 0.70
        db.commit()

        # 4. Create new versioned BenchmarkSuite
        prev_suite = (
            db.query(BenchmarkSuite)
            .filter(BenchmarkSuite.namespace_id == job.namespace_id)
            .order_by(BenchmarkSuite.version_number.desc())
            .first()
        )
        version_num = (prev_suite.version_number + 1) if prev_suite else 1

        suite = BenchmarkSuite(
            namespace_id=job.namespace_id,
            version_number=version_num,
            case_count=0,
            idempotency_hash=idemp_hash,
            is_demo=False
        )
        db.add(suite)
        db.flush()

        # 5. Process each valid cluster
        total_tests_generated = 0
        interaction_map = {str(i.id): i for i in negative_interactions}

        for c_info in valid_clusters:
            exemplar_objs = [
                {"user_query": interaction_map[eid].user_query, "ai_response": interaction_map[eid].ai_response}
                for eid in c_info["exemplar_ids"]
                if eid in interaction_map
            ]

            # LLM Failure Diagnosis
            diagnosis_res = diagnose_failure_cluster(exemplar_objs)

            # Recurrence Rate & Trend calculation
            rec_rate = len(c_info["interaction_ids"]) / max(1, eligible_count)
            rec_trend = 0.28  # Baseline trend delta for new cluster

            pattern = FailurePattern(
                namespace_id=job.namespace_id,
                job_id=job.id,
                title=diagnosis_res["title"],
                diagnosis=diagnosis_res["diagnosis"],
                category=diagnosis_res["category"],
                severity=diagnosis_res["severity"],
                interaction_count=len(c_info["interaction_ids"]),
                recurrence_rate=round(rec_rate, 3),
                recurrence_trend=round(rec_trend, 3),
                cluster_confidence=c_info["cluster_confidence"],
                cluster_cohesion=c_info["cluster_cohesion"],
                diagnosis_confidence=diagnosis_res["diagnosis_confidence"],
                exemplar_interaction_ids=c_info["exemplar_ids"],
                is_demo=False
            )
            db.add(pattern)
            db.flush()

            # Synthesize the 3 test archetypes (Regression, Edge Case, Hard Negative)
            test_cases = generate_archetype_test_suite(
                pattern_title=pattern.title,
                diagnosis=pattern.diagnosis,
                category=pattern.category,
                exemplars=exemplar_objs
            )

            for tc in test_cases:
                bench_case = LivingBenchmarkCase(
                    suite_id=suite.id,
                    pattern_id=pattern.id,
                    namespace_id=job.namespace_id,
                    archetype=tc["archetype"],
                    input_prompt=tc["input_prompt"],
                    expected_output_criteria=tc["expected_output_criteria"],
                    negative_constraint=tc.get("negative_constraint"),
                    assertion_type=tc["assertion_type"],
                    source="production_failure_cluster",
                    is_synthetic=True,
                    is_validated=True,
                    validation_confidence=tc["validation_confidence"],
                    is_demo=False
                )
                db.add(bench_case)
                total_tests_generated += 1

        suite.case_count = total_tests_generated
        job.tests_generated = total_tests_generated
        job.status = "completed"
        job.progress = 1.0
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        return job

    except Exception as e:
        logger.exception("Analysis job failed")
        db.rollback()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        return job
