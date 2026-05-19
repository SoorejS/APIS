from sqlalchemy.orm import Session
import uuid
from backend.models.models import FailureMemory

class FailureMemoryService:
    @staticmethod
    def record_failure(
        db: Session,
        namespace_id: uuid.UUID,
        failed_pattern: str,
        attempted_fix: str,
        reason: str,
        evaluation_result: str = "rejected"
    ) -> FailureMemory:
        """
        Record a failed prompt optimization candidate in the database.
        """
        failure = FailureMemory(
            namespace_id=namespace_id,
            failed_pattern=failed_pattern,
            attempted_fix=attempted_fix,
            reason=reason,
            evaluation_result=evaluation_result
        )
        db.add(failure)
        db.commit()
        db.refresh(failure)
        return failure

    @staticmethod
    def get_failures(db: Session, namespace_id: uuid.UUID) -> list:
        """
        Fetch all historical failures for a given namespace.
        """
        return db.query(FailureMemory).filter(
            FailureMemory.namespace_id == namespace_id
        ).order_by(FailureMemory.created_at.desc()).all()

    @staticmethod
    def get_formatted_failures_prompt(db: Session, namespace_id: uuid.UUID) -> str:
        """
        Formulate a clean prompt instruction detailing historical failure patterns to avoid repeating them.
        """
        failures = FailureMemoryService.get_failures(db, namespace_id)
        if not failures:
            return ""

        instruction = "\n=== HISTORICAL FAILURE MEMORY (AVOID REPEATING THESE MISTAKES) ===\n"
        for idx, f in enumerate(failures[:5]):  # limit to top 5 recent failures to prevent token bloat
            instruction += (
                f"{idx + 1}. Failed Pattern Identified: '{f.failed_pattern}'\n"
                f"   Attempted Fix: '{f.attempted_fix}'\n"
                f"   Reason for Rejection: {f.reason}\n\n"
            )
        instruction += "Ensure your candidate rewrite does NOT repeat the mistakes listed above.\n=================================================================\n"
        return instruction
