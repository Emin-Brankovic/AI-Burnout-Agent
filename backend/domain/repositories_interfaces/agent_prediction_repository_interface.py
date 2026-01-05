"""AgentPrediction repository interface."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from backend.domain.entities.agent_prediction import AgentPredictionEntity


class AgentPredictionRepositoryInterface(ABC):
    """Interface for AgentPrediction repository operations."""

    @abstractmethod
    def add(self, entity: AgentPredictionEntity) -> AgentPredictionEntity:
        """Add a new prediction."""
        pass

    @abstractmethod
    def get_by_id(self, prediction_id: int) -> Optional[AgentPredictionEntity]:
        """Get prediction by ID."""
        pass

    @abstractmethod
    def get_by_daily_log(self, daily_log_id: int) -> List[AgentPredictionEntity]:
        """Get all predictions for a daily log."""
        pass

    @abstractmethod
    def get_by_type(self, prediction_type: str) -> List[AgentPredictionEntity]:
        """Get all predictions of a specific type."""
        pass

    @abstractmethod
    def get_all(self) -> List[AgentPredictionEntity]:
        """Get all predictions."""
        pass

    @abstractmethod
    def update(self, entity: AgentPredictionEntity) -> AgentPredictionEntity:
        """Update existing prediction."""
        pass

    @abstractmethod
    def delete(self, prediction_id: int) -> bool:
        """Delete prediction by ID."""
        pass

    @abstractmethod
    def get_pending_reviews(self) -> List[AgentPredictionEntity]:
        """Fetch all predictions that require HR attention."""
        pass

    @abstractmethod
    def get_validated_since(self, since: datetime) -> List[AgentPredictionEntity]:
        """Fetch samples where HR has validated AI predictions since a certain date."""
        pass
