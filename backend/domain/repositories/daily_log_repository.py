"""DailyLog repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from backend.domain.entities.daily_log import DailyLogEntity


class DailyLogRepositoryInterface(ABC):
    """Interface for DailyLog repository operations."""

    @abstractmethod
    def add(self, entity: DailyLogEntity) -> DailyLogEntity:
        """Add a new daily log."""
        pass

    @abstractmethod
    def get_by_id(self, log_id: int) -> Optional[DailyLogEntity]:
        """Get daily log by ID."""
        pass

    @abstractmethod
    def get_by_employee(self, employee_id: int) -> List[DailyLogEntity]:
        """Get all logs for an employee."""
        pass

    @abstractmethod
    def get_by_date_range(self, employee_id: int, start_date: datetime, end_date: datetime) -> List[DailyLogEntity]:
        """Get logs for employee within date range."""
        pass

    @abstractmethod
    def get_all(self) -> List[DailyLogEntity]:
        """Get all daily logs."""
        pass

    @abstractmethod
    def update(self, entity: DailyLogEntity) -> DailyLogEntity:
        """Update existing daily log."""
        pass

    @abstractmethod
    def delete(self, log_id: int) -> bool:
        """Delete daily log by ID."""
        pass
