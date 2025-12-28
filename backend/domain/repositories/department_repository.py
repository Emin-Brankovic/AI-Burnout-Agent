"""Department repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from backend.domain.entities.department import DepartmentEntity


class DepartmentRepositoryInterface(ABC):
    """Interface for Department repository operations."""

    @abstractmethod
    def add(self, entity: DepartmentEntity) -> DepartmentEntity:
        """Add a new department."""
        pass

    @abstractmethod
    def get_by_id(self, department_id: int) -> Optional[DepartmentEntity]:
        """Get department by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[DepartmentEntity]:
        """Get department by name."""
        pass

    @abstractmethod
    def get_all(self) -> List[DepartmentEntity]:
        """Get all departments."""
        pass

    @abstractmethod
    def update(self, entity: DepartmentEntity) -> DepartmentEntity:
        """Update existing department."""
        pass

    @abstractmethod
    def delete(self, department_id: int) -> bool:
        """Delete department by ID."""
        pass
