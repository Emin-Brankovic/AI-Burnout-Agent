from typing import List, Optional
from sqlalchemy.orm import Session
from backend.domain.repositories_interfaces.model_version_repository_interface import ModelVersionRepositoryInterface
from backend.domain.entities.model_version import ModelVersionEntity
from backend.infrastructure.persistence.database import ModelVersion
from backend.infrastructure.persistence.data_mappers import (
    model_version_model_to_entity,
    model_version_entity_to_model
)

class ModelVersionRepository(ModelVersionRepositoryInterface):
    """SQLAlchemy implementation of ModelVersionRepository."""

    def __init__(self, session: Session):
        self.session = session
        self._identity_map = {}

    def add(self, entity: ModelVersionEntity) -> ModelVersionEntity:
        """Add a new model version."""
        try:
            model = model_version_entity_to_model(entity)
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

    def get_by_version(self, version_number: str) -> Optional[ModelVersionEntity]:
        """Get model version by version string."""
        model = self.session.query(ModelVersion).filter(
            ModelVersion.version_number == version_number
        ).first()

        if model:
            entity = model_version_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None

    def get_latest(self) -> Optional[ModelVersionEntity]:
        """Get the most recent model version."""
        model = self.session.query(ModelVersion).order_by(
            ModelVersion.created_at.desc()
        ).first()

        if model:
            entity = model_version_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None

    def get_all(self) -> List[ModelVersionEntity]:
        """Get all model versions ordered by creation date."""
        models = self.session.query(ModelVersion).order_by(
            ModelVersion.created_at.desc()
        ).all()
        return [model_version_model_to_entity(model) for model in models]
