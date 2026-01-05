from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.domain.repositories_interfaces.agent_prediction_repository_interface import AgentPredictionRepositoryInterface
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.infrastructure.persistence.database import AgentPrediction
from backend.infrastructure.persistence.data_mappers import (
    agent_prediction_model_to_entity,
    agent_prediction_entity_to_model
)


class AgentPredictionRepository(AgentPredictionRepositoryInterface):
    """SQLAlchemy implementation of AgentPredictionRepository."""

    def __init__(self, session: Session):
        self.session = session
        self._identity_map = {}

    def add(self, entity: AgentPredictionEntity) -> AgentPredictionEntity:
        """Add a new prediction."""
        try:
            model = agent_prediction_entity_to_model(entity)
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

    def get_by_id(self, prediction_id: int) -> Optional[AgentPredictionEntity]:
        """Get prediction by ID."""
        if prediction_id in self._identity_map:
            return self._identity_map[prediction_id]

        model = self.session.query(AgentPrediction).filter(
            AgentPrediction.id == prediction_id
        ).first()

        if model:
            entity = agent_prediction_model_to_entity(model)
            self._identity_map[entity.id] = entity
            return entity
        return None

    def get_by_daily_log(self, daily_log_id: int) -> List[AgentPredictionEntity]:
        """Get all predictions for a daily log."""
        models = self.session.query(AgentPrediction).filter(
            AgentPrediction.daily_log_id == daily_log_id
        ).order_by(AgentPrediction.created_at.desc()).all()

        return [agent_prediction_model_to_entity(model) for model in models]

    def get_by_type(self, prediction_type: str) -> List[AgentPredictionEntity]:
        """Get all predictions of a specific type."""
        models = self.session.query(AgentPrediction).filter(
            AgentPrediction.prediction_type == prediction_type
        ).order_by(AgentPrediction.created_at.desc()).all()

        return [agent_prediction_model_to_entity(model) for model in models]

    def get_all(self) -> List[AgentPredictionEntity]:
        """Get all predictions."""
        models = self.session.query(AgentPrediction).order_by(
            AgentPrediction.created_at.desc()
        ).all()
        return [agent_prediction_model_to_entity(model) for model in models]

    def update(self, entity: AgentPredictionEntity) -> AgentPredictionEntity:
        """Update existing prediction."""
        try:
            model = self.session.query(AgentPrediction).filter(
                AgentPrediction.id == entity.id
            ).first()

            if model:
                model.daily_log_id = entity.daily_log_id
                model.prediction_type = entity.prediction_type
                model.prediction_value = entity.prediction_value
                model.confidence_score = entity.confidence_score
                model.needs_review = entity.needs_review
                model.human_validation = entity.human_validation
                model.review_notes = entity.review_notes
                model.reviewed_at = entity.reviewed_at
                
                self.session.flush()
                self.session.commit()
                self._identity_map[entity.id] = entity

            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, prediction_id: int) -> bool:
        """Delete prediction by ID."""
        try:
            model = self.session.query(AgentPrediction).filter(
                AgentPrediction.id == prediction_id
            ).first()

            if model:
                self.session.delete(model)
                self.session.commit()
                if prediction_id in self._identity_map:
                    del self._identity_map[prediction_id]
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e

    def get_pending_reviews(self) -> List[AgentPredictionEntity]:
        """Fetch all predictions that require HR attention."""
        models = self.session.query(AgentPrediction).filter(
            AgentPrediction.needs_review == True
        ).order_by(AgentPrediction.created_at.desc()).all()
        
        return [agent_prediction_model_to_entity(model) for model in models]

    def get_validated_since(self, since: datetime) -> List[AgentPredictionEntity]:
        """Fetch samples where HR has validated AI predictions since a certain date."""
        models = self.session.query(AgentPrediction).filter(
            AgentPrediction.human_validation != None,
            AgentPrediction.reviewed_at >= since
        ).order_by(AgentPrediction.reviewed_at.desc()).all()
        
        return [agent_prediction_model_to_entity(model) for model in models]
