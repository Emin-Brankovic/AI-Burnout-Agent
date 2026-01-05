from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.domain.enums.enums import DailyLogStatus
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.domain.entities.daily_log import DailyLogEntity
from backend.infrastructure.persistence.database import DailyLog
from backend.infrastructure.persistence.data_mappers import (
    daily_log_model_to_entity,
    daily_log_entity_to_model
)


class DailyLogRepository(DailyLogRepositoryInterface):
    """SQLAlchemy implementation of DailyLogRepository."""

    def __init__(self, session: Session):
        self.session = session
        self._identity_map = {}

    def add(self, entity: DailyLogEntity) -> DailyLogEntity:
        """Add a new daily log."""
        try:
            model = daily_log_entity_to_model(entity)
            self.session.add(model)
            self.session.flush()
            self.session.commit()
            entity.id = model.id
            self._identity_map[entity.id] = entity
            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_id(self, log_id: int) -> Optional[DailyLogEntity]:
        """Get daily log by ID."""
        if log_id in self._identity_map:
            return self._identity_map[log_id]

        model = self.session.query(DailyLog).filter(
            DailyLog.id == log_id
        ).first()

        if model:
            entity = daily_log_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None

    def get_by_employee(self, employee_id: int) -> List[DailyLogEntity]:
        """Get all logs for an employee."""
        models = self.session.query(DailyLog).filter(
            DailyLog.employee_id == employee_id
        ).order_by(DailyLog.log_date.desc()).all()

        return [daily_log_model_to_entity(model) for model in models]

    def get_by_date_range(
        self,
        employee_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[DailyLogEntity]:
        """Get logs for employee within date range."""
        models = self.session.query(DailyLog).filter(
            DailyLog.employee_id == employee_id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date
        ).order_by(DailyLog.log_date.desc()).all()

        return [daily_log_model_to_entity(model) for model in models]

    def get_all(self) -> List[DailyLogEntity]:
        """Get all daily logs."""
        models = self.session.query(DailyLog).order_by(
            DailyLog.log_date.desc()
        ).all()
        return [daily_log_model_to_entity(model) for model in models]

    def update(self, entity: DailyLogEntity) -> DailyLogEntity:
        """Update existing daily log."""
        try:
            model = self.session.query(DailyLog).filter(
                DailyLog.id == entity.id
            ).first()

            if model:
                model.employee_id = entity.employee_id
                model.log_date = entity.log_date
                model.hours_worked = entity.hours_worked
                model.hours_slept = entity.hours_slept
                model.daily_personal_time = entity.daily_personal_time
                model.motivation_level = entity.motivation_level
                model.stress_level = entity.stress_level
                model.workload_intensity = entity.workload_intensity
                model.overtime_hours_today = entity.overtime_hours_today
                self.session.flush()
                self.session.commit()
                self._identity_map[entity.id] = entity

            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, log_id: int) -> bool:
        """Delete daily log by ID."""
        try:
            model = self.session.query(DailyLog).filter(
                DailyLog.id == log_id
            ).first()

            if model:
                self.session.delete(model)
                self.session.commit()
                if log_id in self._identity_map:
                    del self._identity_map[log_id]
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e

    def get_all_by_status(
            self,
            status: DailyLogStatus,
            limit: int = 100
    ) -> List[DailyLogEntity]:
        """Get all logs with specific status."""
        models = (
            self.session.query(DailyLog)
            .filter(DailyLog.status == status.value)
            .order_by(DailyLog.log_date.desc())
            .limit(limit)
            .all()
        )
        return [daily_log_model_to_entity(model) for model in models]

    def get_pending_for_employee(
            self,
            employee_id: int,
            days: int = 7
    ) -> List[DailyLogEntity]:
        """Get pending logs for employee within timeframe."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        models = (
            self.session.query(DailyLog)
            .filter(
                DailyLog.employee_id == employee_id,
                DailyLog.status == DailyLogStatus.PENDING.value,
                DailyLog.log_date >= cutoff_date
            )
            .order_by(DailyLog.log_date.desc())
            .all()
        )
        return [daily_log_model_to_entity(model) for model in models]

    def count_by_status(self, status: DailyLogStatus) -> int:
        """Count logs with specific status."""
        return (
            self.session.query(func.count(DailyLog.id))
            .filter(DailyLog.status == status.value)
            .scalar()
        )

    def get_next_pending(self) -> Optional[DailyLogEntity]:
        """Get next pending log ordered by date (FIFO)."""
        model = (
            self.session.query(DailyLog)
            .filter(DailyLog.status == DailyLogStatus.PENDING.value)
            .order_by(DailyLog.log_date.asc())
            .first()
        )

        if model:
            return daily_log_model_to_entity(model)
        return None

    def get_queue_statistics(self) -> dict:
        """Get statistics for all statuses."""
        total = self.session.query(func.count(DailyLog.id)).scalar()

        return {
            "total_logs": total,
            "pending": self.count_by_status(DailyLogStatus.QUEUED),
            "processing": self.count_by_status(DailyLogStatus.PROCESSING),
            "analyzed": self.count_by_status(DailyLogStatus.ANALYZED),
            "pending_review": self.count_by_status(DailyLogStatus.PENDING_REVIEW),
            "reviewed": self.count_by_status(DailyLogStatus.REVIEWED),
            "failed": self.count_by_status(DailyLogStatus.FAILED)
        }
