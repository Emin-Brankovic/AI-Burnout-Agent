from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.entities.model_version import ModelVersionEntity

class ModelVersionRepositoryInterface(ABC):
    """Interface for ModelVersion repository operations."""

    @abstractmethod
    def add(self, entity: ModelVersionEntity) -> ModelVersionEntity:
        """Add a new model version."""
        pass

    @abstractmethod
    def get_by_version(self, version_number: str) -> Optional[ModelVersionEntity]:
        """Get model version by version string."""
        pass

    @abstractmethod
    def get_latest(self) -> Optional[ModelVersionEntity]:
        """Get the most recent model version."""
        pass

    @abstractmethod
    def get_all(self) -> List[ModelVersionEntity]:
        """Get all model versions ordered by creation date."""
        pass
