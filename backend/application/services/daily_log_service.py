from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.application.services.base_crud_service import BaseCRUDService
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository


class DailyLogService(BaseCRUDService[
                          DailyLogEntity,
                          DailyLogRepositoryInterface,
                          Dict[str, Any],
                          Dict[str, Any]
                      ]):
    """DailyLog service with CRUD operations."""

    def __init__(self, session: Session):
        repository = DailyLogRepository(session)
        super().__init__(session, repository)

    def map_insert_to_entity(self, request: Dict[str, Any]) -> DailyLogEntity:
        """Map insert request to DailyLogEntity."""
        return DailyLogEntity(
            employee_id=request['employee_id'],
            log_date=request.get('log_date', datetime.now()),
            hours_worked=request.get('hours_worked'),
            hours_slept=request.get('hours_slept'),
            daily_personal_time=request.get('daily_personal_time'),
            motivation_level=request.get('motivation_level'),
            stress_level=request.get('stress_level'),
            workload_intensity=request.get('workload_intensity'),
            overtime_hours_today=request.get('overtime_hours_today')
        )

    def map_update_to_entity(
            self,
            entity: DailyLogEntity,
            request: Dict[str, Any]
    ) -> DailyLogEntity:
        """Map update request to DailyLogEntity."""
        if 'log_date' in request:
            entity.log_date = request['log_date']
        if 'hours_worked' in request:
            entity.hours_worked = request['hours_worked']
        if 'hours_slept' in request:
            entity.hours_slept = request['hours_slept']
        if 'daily_personal_time' in request:
            entity.daily_personal_time = request['daily_personal_time']
        if 'motivation_level' in request:
            entity.motivation_level = request['motivation_level']
        if 'stress_level' in request:
            entity.stress_level = request['stress_level']
        if 'workload_intensity' in request:
            entity.workload_intensity = request['workload_intensity']
        if 'overtime_hours_today' in request:
            entity.overtime_hours_today = request['overtime_hours_today']

        return entity

    def get_by_employee(self, employee_id: int) -> List[DailyLogEntity]:
        """Get all logs for an employee."""
        return self.repository.get_by_employee(employee_id)

    def get_by_date_range(
            self,
            employee_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> List[DailyLogEntity]:
        """Get logs for employee within date range."""
        return self.repository.get_by_date_range(employee_id, start_date, end_date)
