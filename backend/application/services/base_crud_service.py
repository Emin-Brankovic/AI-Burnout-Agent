from typing import TypeVar, Generic, Optional
from abc import abstractmethod
from sqlalchemy.orm import Session
from backend.application.services.base_service import BaseService, BaseSearchObject

# Type variables
TEntity = TypeVar('TEntity')
TRepository = TypeVar('TRepository')
TInsert = TypeVar('TInsert')
TUpdate = TypeVar('TUpdate')


class BaseCRUDService(
    BaseService[TEntity, TRepository],
    Generic[TEntity, TRepository, TInsert, TUpdate]
):
    """Base CRUD service with create, update, delete operations."""

    def __init__(self, session: Session, repository: TRepository):
        super().__init__(session, repository)

    def create(self, request: TInsert) -> TEntity:

        # Map insert request to domain entity (uses your existing entity classes)
        entity = self.map_insert_to_entity(request)

        # Hook for custom logic before insert (validation, etc.)
        self.before_insert(entity, request)

        # Add to repository (uses your existing repository)
        created_entity = self.repository.add(entity)

        # Commit transaction
        self.session.commit()

        return created_entity

    def update(self, entity_id: int, request: TUpdate) -> Optional[TEntity]:

        # Get existing entity from repository
        entity = self.repository.get_by_id(entity_id)
        if entity is None:
            raise ValueError(f"Entity with ID {entity_id} not found")

        # Hook for custom logic before update
        self.before_update(entity, request)

        # Map update request to entity
        updated_entity = self.map_update_to_entity(entity, request)

        # Update in repository (uses your existing repository)
        result = self.repository.update(updated_entity)

        # Commit transaction
        self.session.commit()

        return result

    def delete(self, entity_id: int) -> bool:

        # Get existing entity
        entity = self.repository.get_by_id(entity_id)
        if entity is None:
            raise ValueError(f"Entity with ID {entity_id} not found")

        # Hook for custom logic before delete
        self.before_delete(entity)

        # Delete from repository (uses your existing repository)
        success = self.repository.delete(entity_id)

        # Commit transaction
        self.session.commit()

        return success

    @abstractmethod
    def map_insert_to_entity(self, request: TInsert) -> TEntity:
        """
        Map insert request to domain entity.
        Must be implemented by subclasses.
        Creates new entity from request data.
        """
        pass

    @abstractmethod
    def map_update_to_entity(self, entity: TEntity, request: TUpdate) -> TEntity:
        """
        Map update request to existing entity.
        Must be implemented by subclasses.
        Updates entity fields from request data.
        """
        pass

    def before_insert(self, entity: TEntity, request: TInsert) -> None:
        """
        Hook called before inserting entity.
        Override to add custom logic (validation, defaults, etc.).
        """
        pass

    def before_update(self, entity: TEntity, request: TUpdate) -> None:
        """
        Hook called before updating entity.
        Override to add custom logic.
        """
        pass

    def before_delete(self, entity: TEntity) -> None:
        """
        Hook called before deleting entity.
        Override to add custom logic (cascade deletes, checks, etc.).
        """
        pass
