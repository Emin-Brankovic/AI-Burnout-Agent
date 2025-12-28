from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.domain.repositories.daily_log_repository import DailyLogRepositoryInterface
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
        model = daily_log_entity_to_model(entity)
        self.session.add(model)
        self.session.flush()
        entity.id = model.id
        self._identity_map[entity.id] = entity
        return entity

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
            self._identity_map[entity.id] = entity

        return entity

    def delete(self, log_id: int) -> bool:
        """Delete daily log by ID."""
        model = self.session.query(DailyLog).filter(
            DailyLog.id == log_id
        ).first()

        if model:
            self.session.delete(model)
            if log_id in self._identity_map:
                del self._identity_map[log_id]
            return True
        return False
