"""
Queue Service for Burnout Detection System

Manages daily log processing queue with real database operations.
Handles the lifecycle: PENDING → PROCESSING → ANALYZED → REVIEWED
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.enums.enums import DailyLogStatus
from backend.infrastructure.persistence.data_mappers import daily_log_entity_to_model, daily_log_model_to_entity
from backend.infrastructure.persistence.database import DailyLog, Employee


class DailyLogQueueService:
    """
    Service for queue operations on daily logs - WITH REAL DB!

    Responsibilities:
    - Enqueue new daily logs for agent analysis
    - Dequeue next pending log for processing
    - Update log status through agent lifecycle
    - Track queue metrics and failures
    """

    def __init__(self, db_session: Session):
        """
        Initialize queue service

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    async def enqueue(self, entity: DailyLogEntity) -> DailyLogEntity:
        """
        Add daily log to queue for agent analysis (SAVE TO DB).

        Args:
            entity: DailyLogEntity from domain layer

        Returns:
            Saved DailyLogEntity with assigned ID
        """
        # Convert domain entity to database model using mapper
        db_model = daily_log_entity_to_model(entity)

        # Save to database
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)

        # Convert back to domain entity using mapper
        saved_entity = daily_log_model_to_entity(db_model)

        print(f"📥 Enqueued daily log: Employee {saved_entity.employee_id} "
              f"(Date: {saved_entity.log_date.date()}, ID: {saved_entity.id})")

        return saved_entity

    async def dequeue_next(self, status: DailyLogStatus = DailyLogStatus.QUEUED) -> Optional[DailyLog]:
        """
        Get next daily log from queue for processing.

        Args:
            status: Status to filter by (default: PENDING)

        Returns:
            Next DailyLog or None if queue is empty
        """
        # Query for next log with given status, ordered by date
        daily_log = (
            self.db.query(DailyLog)
            .filter(DailyLog.status == status.value)
            .order_by(DailyLog.log_date.asc())
            .first()
        )

        if not daily_log:
            return None

        print(f"📤 Dequeued daily log: Employee {daily_log.employee_id} (ID: {daily_log.id})")

        return daily_log

    async def update_status(
            self,
            log_id: int,
            new_status: DailyLogStatus,
            processed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update daily log status.

        Args:
            log_id: Daily log ID
            new_status: New status
            processed_at: Optional processing timestamp

        Returns:
            True if update successful, False otherwise
        """
        daily_log = self.db.query(DailyLog).filter(DailyLog.id == log_id).first()

        if not daily_log:
            print(f"⚠️ Daily log {log_id} not found")
            return False

        daily_log.status = new_status.value

        # Update processed timestamp if provided
        daily_log.processed_at = processed_at

        self.db.commit()

        print(f"🔄 Updated daily log {log_id} status: {new_status.value}")
        return True

    async def mark_as_failed(self, log_id: int, error: str) -> bool:
        """
        Mark log as FAILED due to processing error.

        Args:
            log_id: Daily log ID
            error: Error message

        Returns:
            True if successful
        """
        print(f"❌ Daily log {log_id} failed: {error}")

        # Optionally store error message in database
        daily_log = self.db.query(DailyLog).filter(DailyLog.id == log_id).first()
        if daily_log and hasattr(daily_log, 'error_message'):
            daily_log.error_message = error
            self.db.commit()

        return await self.update_status(log_id, DailyLogStatus.FAILED)

    async def get_queue_size(self, status: DailyLogStatus = DailyLogStatus.QUEUED) -> int:
        """
        Get number of logs in queue with given status.

        Args:
            status: Status to count

        Returns:
            Number of logs
        """

        return self.db.query(DailyLog).filter(DailyLog.status == status.value).count()

    async def get_queue_stats(self) -> dict:
        """
        Get comprehensive queue statistics.
        """
        stats = {
            "total": self.db.query(DailyLog).count(),
            "queued": await self.get_queue_size(DailyLogStatus.QUEUED),
            "processing": await self.get_queue_size(DailyLogStatus.PROCESSING),
            "analyzed": await self.get_queue_size(DailyLogStatus.ANALYZED),
            "pending_review": await self.get_queue_size(DailyLogStatus.PENDING_REVIEW),
            "reviewed": await self.get_queue_size(DailyLogStatus.REVIEWED),
            "failed": await self.get_queue_size(DailyLogStatus.FAILED)
        }
        return stats



# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("✅ DailyLogQueueService loaded")
    print("\n📋 Available Operations:")
    print("   - enqueue(): Add new daily log")
    print("   - dequeue_next(): Get next log for processing")
    print("   - mark_as_processing(): Start processing")
    print("   - mark_as_analyzed(): Finish analysis")
    print("   - mark_as_failed(): Handle errors")
    print("   - get_queue_stats(): Get metrics")
