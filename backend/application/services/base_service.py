from typing import TypeVar, Generic, List, Optional
from abc import ABC
from sqlalchemy.orm import Session
from dataclasses import dataclass

# Type variables
TEntity = TypeVar('TEntity')  # Domain Entity
TRepository = TypeVar('TRepository')  # Repository Interface


@dataclass
class PagedResult(Generic[TEntity]):
    """Paged result container."""
    items: List[TEntity]
    count: int
    page: Optional[int] = None
    page_size: Optional[int] = None


@dataclass
class BaseSearchObject:
    """Base search object with pagination."""
    page: Optional[int] = None
    page_size: Optional[int] = None


class BaseService(ABC, Generic[TEntity, TRepository]):
    """Base service for read operations."""

    def __init__(self, session: Session, repository: TRepository):
        self.session = session
        self.repository = repository

    def get_all(self, search: Optional[BaseSearchObject] = None) -> PagedResult[TEntity]:
        # Get all entities from repository
        all_entities = self.repository.get_all()

        # Apply custom filters if provided
        if search:
            all_entities = self.apply_filter(all_entities, search)

        # Get total count
        total_count = len(all_entities)

        # Apply pagination
        items = all_entities
        if search and search.page is not None and search.page_size is not None:
            skip = (search.page - 1) * search.page_size
            items = all_entities[skip:skip + search.page_size]

        return PagedResult(
            items=items,
            count=total_count,
            page=search.page if search else None,
            page_size=search.page_size if search else None
        )

    def get_by_id(self, entity_id: int) -> Optional[TEntity]:
        entity = self.repository.get_by_id(entity_id)
        if entity is None:
            raise ValueError(f"Entity with ID {entity_id} not found")
        return entity

    def apply_filter( self, entities: List[TEntity], search: BaseSearchObject) -> List[TEntity]:
        """
        Override to apply custom filters.
        Default implementation returns entities unchanged.
        """
        return entities
