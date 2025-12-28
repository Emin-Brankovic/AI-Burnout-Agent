from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.application.services.base_crud_service import BaseCRUDService, BaseSearchObject
from backend.domain.entities.employee import EmployeeEntity
from backend.domain.repositories.employee_repository import EmployeeRepositoryInterface
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository


class EmployeeSearchObject(BaseSearchObject):
    """Search object for employees."""

    def __init__(
            self,
            department_id: int = None,
            email: str = None,
            page: int = None,
            page_size: int = None
    ):
        super().__init__(page, page_size)
        self.department_id = department_id
        self.email = email


class EmployeeService(BaseCRUDService[
                          EmployeeEntity,
                          EmployeeRepositoryInterface,
                          Dict[str, Any],  # Insert request as dict
                          Dict[str, Any]  # Update request as dict
                      ]):
    """Employee service with CRUD operations."""

    def __init__(self, session: Session):
        repository = EmployeeRepository(session)
        super().__init__(session, repository)

    # Mapping uses your existing EmployeeEntity class
    def map_insert_to_entity(self, request: Dict[str, Any]) -> EmployeeEntity:
        """Map insert request dict to EmployeeEntity."""
        return EmployeeEntity(
            first_name=request['first_name'],
            last_name=request['last_name'],
            email=request['email'],
            department_id=request.get('department_id'),
            hire_date=datetime.now()
        )

    def map_update_to_entity(
            self,
            entity: EmployeeEntity,
            request: Dict[str, Any]
    ) -> EmployeeEntity:
        """Map update request dict to existing EmployeeEntity."""
        # Update only provided fields
        if 'first_name' in request and request['first_name'] is not None:
            entity.first_name = request['first_name']
        if 'last_name' in request and request['last_name'] is not None:
            entity.last_name = request['last_name']
        if 'email' in request and request['email'] is not None:
            entity.email = request['email']
        if 'department_id' in request:
            entity.department_id = request['department_id']

        return entity

    def before_insert(self, entity: EmployeeEntity, request: Dict[str, Any]) -> None:
        """Validate before insert - uses your existing repository."""
        # Check if email already exists
        existing = self.repository.get_by_email(entity.email)
        if existing:
            raise ValueError(f"Employee with email {entity.email} already exists")

    def before_update(self, entity: EmployeeEntity, request: Dict[str, Any]) -> None:
        """Validate before update - uses your existing repository."""
        # Check email uniqueness if changing
        if 'email' in request and request['email'] != entity.email:
            existing = self.repository.get_by_email(request['email'])
            if existing:
                raise ValueError(f"Email {request['email']} is already in use")

    def apply_filter(
            self,
            entities: List[EmployeeEntity],
            search: EmployeeSearchObject
    ) -> List[EmployeeEntity]:
        """Apply custom filters."""
        filtered = entities

        if search.department_id:
            filtered = [e for e in filtered if e.department_id == search.department_id]

        if search.email:
            filtered = [e for e in filtered if search.email.lower() in e.email.lower()]

        return filtered

    def get_by_department(self, department_id: int) -> List[EmployeeEntity]:
        """Get employees by department - uses your existing repository method."""
        return self.repository.get_by_department(department_id)

    def get_by_email(self, email: str) -> EmployeeEntity:
        """Get employee by email - uses your existing repository method."""
        employee = self.repository.get_by_email(email)
        if not employee:
            raise ValueError(f"Employee with email {email} not found")
        return employee
