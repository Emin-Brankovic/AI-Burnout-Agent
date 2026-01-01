from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.application.services.base_crud_service import BaseCRUDService
from backend.domain.entities.department import DepartmentEntity
from backend.domain.repositories_interfaces.department_repository_interface import DepartmentRepositoryInterface
from backend.infrastructure.persistence.repositories.department_repository import DepartmentRepository
from backend.presentation.schemas.department_schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest
)


class DepartmentService(BaseCRUDService[
                            DepartmentEntity,
                            DepartmentRepositoryInterface,
                            DepartmentCreateRequest,  # ← Pydantic object, not dict
                            DepartmentUpdateRequest
                        ]):
    """Department service with CRUD operations."""

    def __init__(self, session: Session):
        repository = DepartmentRepository(session)
        super().__init__(session, repository)

    def map_insert_to_entity(self, request: DepartmentCreateRequest) -> DepartmentEntity:
        """Map Pydantic DTO to DepartmentEntity."""
        return DepartmentEntity(
            name=request.name,  # ✅ Use .attribute not ['key']
            description=request.description,
            created_at=datetime.now()
        )

    def map_update_to_entity(
            self,
            entity: DepartmentEntity,
            request: DepartmentUpdateRequest
    ) -> DepartmentEntity:
        """Map update request to DepartmentEntity."""
        if request.name is not None:
            entity.name = request.name
        if request.description is not None:
            entity.description = request.description

        return entity

    def before_insert(self, entity: DepartmentEntity, request: DepartmentCreateRequest) -> None:
        """Validate before insert."""
        existing = self.repository.get_by_name(entity.name)
        if existing:
            raise ValueError(f"Department with name {entity.name} already exists")

    def get_by_name(self, name: str) -> DepartmentEntity:
        """Get department by name."""
        department = self.repository.get_by_name(name)
        if not department:
            raise ValueError(f"Department with name {name} not found")
        return department
