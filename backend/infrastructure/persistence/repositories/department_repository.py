from typing import Optional, List
from sqlalchemy.orm import Session
from backend.domain.repositories_interfaces.department_repository_interface import DepartmentRepositoryInterface
from backend.domain.entities.department import DepartmentEntity
from backend.infrastructure.persistence.database import Department
from backend.infrastructure.persistence.data_mappers import (
    department_model_to_entity,
    department_entity_to_model
)


class DepartmentRepository(DepartmentRepositoryInterface):
    """SQLAlchemy implementation of DepartmentRepository."""

    def __init__(self, session: Session):
        self.session = session
        self._identity_map = {}

    def add(self, entity: DepartmentEntity) -> DepartmentEntity:
        """Add a new department."""
        try:
            model = department_entity_to_model(entity)
            self.session.add(model)
            self.session.flush()
            self.session.commit()
            entity.id = model.id
            entity.created_at = model.created_at
            self._identity_map[entity.id] = entity
            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_id(self, department_id: int) -> Optional[DepartmentEntity]:
        """Get department by ID."""
        if department_id in self._identity_map:
            return self._identity_map[department_id]

        model = self.session.query(Department).filter(
            Department.id == department_id
        ).first()

        if model:
            entity = department_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None

    def get_by_name(self, name: str) -> Optional[DepartmentEntity]:
        """Get department by name."""
        model = self.session.query(Department).filter(
            Department.name == name
        ).first()

        if model:
            entity = department_model_to_entity(model)
            if entity.id not in self._identity_map:
                self._identity_map[entity.id] = entity
            return entity
        return None

    def get_all(self) -> List[DepartmentEntity]:
        """Get all departments."""
        models = self.session.query(Department).all()
        return [department_model_to_entity(model) for model in models]

    def update(self, entity: DepartmentEntity) -> DepartmentEntity:
        """Update existing department."""
        try:
            model = self.session.query(Department).filter(
                Department.id == entity.id
            ).first()

            if model:
                model.name = entity.name
                model.description = entity.description
                self.session.flush()
                self.session.commit()
                self._identity_map[entity.id] = entity

            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, department_id: int) -> bool:
        """Delete department by ID."""
        try:
            model = self.session.query(Department).filter(
                Department.id == department_id
            ).first()

            if model:
                self.session.delete(model)
                self.session.commit()
                if department_id in self._identity_map:
                    del self._identity_map[department_id]
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e
