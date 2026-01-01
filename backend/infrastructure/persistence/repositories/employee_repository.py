from typing import Optional, List
from sqlalchemy.orm import Session
from backend.domain.repositories_interfaces.employee_repository_interface import EmployeeRepositoryInterface
from backend.domain.entities.employee import EmployeeEntity
from backend.infrastructure.persistence.database import Employee
from backend.infrastructure.persistence.data_mappers import (
    employee_model_to_entity,
    employee_entity_to_model
)


class EmployeeRepository(EmployeeRepositoryInterface):
    """SQLAlchemy implementation of EmployeeRepository."""

    def __init__(self, session: Session):
        self.session = session
        self._identity_map = {}

    def add(self, entity: EmployeeEntity) -> EmployeeEntity:
        """Add new employee to repository."""
        model = employee_entity_to_model(entity)
        self.session.add(model)
        self.session.flush()  # Get ID without committing
        entity.id = model.id
        self._identity_map[entity.id] = entity
        return entity

    def get_by_id(self, employee_id: int) -> Optional[EmployeeEntity]:
        """Get employee by ID."""
        # Check identity map first
        if employee_id in self._identity_map:
            return self._identity_map[employee_id]

        model = self.session.query(Employee).filter(Employee.id == employee_id).first()
        if model:
            entity = employee_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None


    def get_by_department(self, department_id: int) -> List[EmployeeEntity]:
        """Get all employees in a specific department."""
        # Query all employees with matching department_id
        models = self.session.query(Employee).filter(
            Employee.department_id == department_id
        ).all()

        # Convert each ORM model to domain entity
        return [employee_model_to_entity(model) for model in models]

    def get_all(self) -> List[EmployeeEntity]:
        """Get all employees."""
        models = self.session.query(Employee).all()
        return [employee_model_to_entity(model) for model in models]

    def update(self, entity: EmployeeEntity) -> EmployeeEntity:
        """Update existing employee."""
        model = self.session.query(Employee).filter(Employee.id == entity.id).first()
        if model:
            model.first_name = entity.first_name
            model.last_name = entity.last_name
            model.email = entity.email
            model.department_id = entity.department_id
            self.session.flush()
            self._identity_map[entity.id] = entity
        return entity

    def delete(self, employee_id: int) -> bool:
        """Delete employee by ID."""
        model = self.session.query(Employee).filter(Employee.id == employee_id).first()
        if model:
            self.session.delete(model)
            if employee_id in self._identity_map:
                del self._identity_map[employee_id]
            return True
        return False
