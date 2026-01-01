"""Employee repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from backend.domain.entities.employee import EmployeeEntity


class EmployeeRepositoryInterface(ABC):
    """Interface for Employee repository operations."""

    @abstractmethod
    def add(self, entity: EmployeeEntity) -> EmployeeEntity:
        """Add a new employee."""
        pass

    @abstractmethod
    def get_by_id(self, employee_id: int) -> Optional[EmployeeEntity]:
        """Get employee by ID."""
        pass

    # @abstractmethod
    # def get_by_email(self, email: str) -> Optional[EmployeeEntity]:
    #     """Get employee by email."""
    #     pass

    @abstractmethod
    def get_all(self) -> List[EmployeeEntity]:
        """Get all employees."""
        pass

    @abstractmethod
    def get_by_department(self, department_id: int) -> List[EmployeeEntity]:
        """Get all employees in a department."""
        pass

    @abstractmethod
    def update(self, entity: EmployeeEntity) -> EmployeeEntity:
        """Update existing employee."""
        pass

    @abstractmethod
    def delete(self, employee_id: int) -> bool:
        """Delete employee by ID."""
        pass
