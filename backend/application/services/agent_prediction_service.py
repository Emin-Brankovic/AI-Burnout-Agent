from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.application.services.base_crud_service import BaseCRUDService
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.repositories_interfaces.agent_prediction_repository_interface import AgentPredictionRepositoryInterface
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository


class AgentPredictionService(BaseCRUDService[
                                 AgentPredictionEntity,
                                 AgentPredictionRepositoryInterface,
                                 Dict[str, Any],
                                 Dict[str, Any]
                             ]):
    """AgentPrediction service with CRUD operations."""

    def __init__(self, session: Session):
        repository = AgentPredictionRepository(session)
        super().__init__(session, repository)

    def map_insert_to_entity(self, request: Dict[str, Any]) -> AgentPredictionEntity:
        """Map insert request to AgentPredictionEntity."""
        return AgentPredictionEntity(
            daily_log_id=request['daily_log_id'],
            burnout_risk=request['burnout_risk'],
            burnout_rate=request.get('burnout_rate'),
            confidence_score=request.get('confidence_score'),
            created_at=datetime.now()
        )

    def map_update_to_entity(
            self,
            entity: AgentPredictionEntity,
            request: Dict[str, Any]
    ) -> AgentPredictionEntity:
        """Map update request to AgentPredictionEntity."""
        if 'daily_log_id' in request:
            entity.daily_log_id = request['daily_log_id']
        if 'burnout_risk' in request:
            entity.burnout_risk = request['burnout_risk']
        if 'burnout_rate' in request:
            entity.burnout_rate = request['burnout_rate']
        if 'confidence_score' in request:
            entity.confidence_score = request['confidence_score']

        return entity

    def before_insert(self, entity: AgentPredictionEntity, request: Dict[str, Any]) -> None:
        """Validate before insert."""
        # Add any custom validation here
        # For example: validate that daily_log exists
        pass

    def get_by_daily_log(self, daily_log_id: int) -> List[AgentPredictionEntity]:
        """Get all predictions for a daily log."""
        return self.repository.get_by_daily_log(daily_log_id)

    def get_by_type(self, burnout_risk: str) -> List[AgentPredictionEntity]:
        """Get all predictions of a specific type."""
        return self.repository.get_by_type(burnout_risk)

    def get_high_confidence_predictions(self, daily_log_id: int) -> List[AgentPredictionEntity]:
        """Get only high confidence predictions for a daily log."""
        predictions = self.repository.get_by_daily_log(daily_log_id)
        return [p for p in predictions if p.is_high_confidence()]
