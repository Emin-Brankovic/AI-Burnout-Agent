"""
Prediction Service

Orchestrates burnout prediction workflow:
- Load trained model
- Make predictions using BurnoutPredictor
- Store predictions in database via AgentPredictionRepository
- Handle batch predictions
- Track prediction history
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from backend.ML.burnout_predictor import BurnoutPredictor, PredictionResult
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.repositories_interfaces.agent_prediction_repository_interface import (
    AgentPredictionRepositoryInterface
)
from backend.domain.enums.enums import BurnoutRiskLevel, DailyLogStatus
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.domain.repositories_interfaces.employee_repository_interface import EmployeeRepositoryInterface
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from backend.application.services.queue_service import DailyLogQueueService
from sqlalchemy.orm import Session


class PredictionService:
    """
    Service for making burnout predictions and persisting results.

    Responsibilities:
    - Load ML model
    - Make predictions on daily logs
    - Convert predictions to domain entities
    - Store predictions in database
    - Retrieve prediction history
    """

    def __init__(
            self,
            predictor: BurnoutPredictor,
            prediction_repository: AgentPredictionRepositoryInterface,
            daily_log_repository: DailyLogRepositoryInterface,
            employee_repository: EmployeeRepositoryInterface,
            queue_service: Optional[DailyLogQueueService] = None,
            model_path: str = 'backend/ml_models/burnout_model.pkl'
    ):
        """
        Initialize prediction service.

        Args:
            predictor: BurnoutPredictor instance
            prediction_repository: Repository for storing predictions
            model_path: Path to trained model file
        """
        self.predictor = predictor
        self.prediction_repository = prediction_repository
        self.model_path = Path(model_path)
        self.daily_log_repository = daily_log_repository
        self.employee_repository = employee_repository
        self.queue_service = queue_service

        # Auto-load model if it exists
        if self.model_path.exists() and not predictor.is_model_loaded:
            self.predictor.load_model(str(self.model_path))
            print(f"✅ Model loaded from {self.model_path}")
        else:
            print(f"⚠️ Model not found at {self.model_path}. Call load_model() manually.")

    # ========== PREDICTION METHODS ==========

    def predict_for_daily_log(
            self,
            daily_log: DailyLogEntity,
            save_to_db: bool = True
    ) -> AgentPredictionEntity:

        if not self.predictor.is_model_loaded:
            raise RuntimeError("Model not loaded. Cannot make predictions.")

        # Make prediction using BurnoutPredictor
        prediction_result: PredictionResult = self.predictor.predict(daily_log)

        # Convert to domain entity
        prediction_entity = self._convert_result_to_entity(
            daily_log=daily_log,
            prediction_result=prediction_result
        )

        # Save to database if requested

        saved_prediction = self.prediction_repository.add(prediction_entity)
        print(f"✅ Prediction saved to database (ID: {saved_prediction.id})")
        return saved_prediction


    def predict_batch(
            self,
            daily_logs: List[DailyLogEntity],
            save_to_db: bool = True
    ) -> List[AgentPredictionEntity]:
        """
        Predict burnout for multiple daily logs.

        Args:
            daily_logs: List of DailyLogEntity instances
            save_to_db: Whether to save predictions to database

        Returns:
            List of AgentPredictionEntity with predictions
        """
        print(f"🔮 Batch prediction for {len(daily_logs)} daily logs...")

        predictions = []

        for daily_log in daily_logs:
            try:
                prediction = self.predict_for_daily_log(daily_log, save_to_db=save_to_db)
                predictions.append(prediction)
            except Exception as e:
                print(f"❌ Failed to predict for log {daily_log.id}: {e}")
                continue

        print(f"✅ Completed {len(predictions)}/{len(daily_logs)} predictions")
        return predictions

    # ========== HELPER METHODS ==========

    def _convert_result_to_entity(
            self,
            daily_log: DailyLogEntity,
            prediction_result: PredictionResult
    ) -> AgentPredictionEntity:
        # Get risk level enum and convert to string for prediction_type
        risk_level_enum = BurnoutRiskLevel.from_burnout_rate(prediction_result.burnout_rate)
        
        entity = AgentPredictionEntity(
            daily_log_id=daily_log.id,
            prediction_type=prediction_result.prediction_type,  # Use from result
            prediction_value=str(round(prediction_result.burnout_rate, 4)),  # Store as string with more precision
            confidence_score=prediction_result.confidence_score,  # Renamed field
            created_at=datetime.utcnow()
        )

        # Message is not stored in DB but useful for processing
        entity.message = prediction_result.message

        return entity

    # ========== RETRIEVAL METHODS ==========

    def get_predictions_for_log(self, daily_log_id: int) -> List[AgentPredictionEntity]:
        """
        Get all predictions for a specific daily log.

        Args:
            daily_log_id: ID of daily log

        Returns:
            List of predictions for that log
        """
        return self.prediction_repository.get_by_daily_log(daily_log_id)

    def get_latest_prediction_for_log(
            self,
            daily_log_id: int
    ) -> Optional[AgentPredictionEntity]:
        """
        Get most recent prediction for a daily log.

        Args:
            daily_log_id: ID of daily log

        Returns:
            Latest prediction or None
        """
        predictions = self.prediction_repository.get_by_daily_log(daily_log_id)

        if predictions:
            return predictions[0]  # Already sorted by created_at desc

        return None

    def get_all_predictions(self) -> List[AgentPredictionEntity]:
        """
        Get all predictions from database.

        Returns:
            List of all predictions
        """
        return self.prediction_repository.get_all()

    def get_predictions_by_type(self, prediction_type: str) -> List[AgentPredictionEntity]:
        """
        Get all predictions with specific type.

        Args:
            prediction_type: Prediction type (NORMAL, MEDIUM, HIGH, CRITICAL)

        Returns:
            List of predictions with that type
        """
        all_predictions = self.prediction_repository.get_all()

        return [
            p for p in all_predictions
            if p.prediction_type == prediction_type
        ]

    # ========== STATISTICS ==========

    def get_prediction_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about predictions.

        Returns:
            Dictionary with prediction statistics
        """
        all_predictions = self.prediction_repository.get_all()

        if not all_predictions:
            return {
                "total_predictions": 0,
                "risk_distribution": {},
                "average_burnout_rate": 0.0
            }

        # Calculate risk distribution
        risk_counts = {}
        total_burnout_rate = 0.0

        for prediction in all_predictions:
            prediction_type = prediction.prediction_type or 'UNKNOWN'
            risk_counts[prediction_type] = risk_counts.get(prediction_type, 0) + 1
            total_burnout_rate += prediction.prediction_value or 0.0

        return {
            "total_predictions": len(all_predictions),
            "risk_distribution": risk_counts,
            "average_burnout_rate": total_burnout_rate / len(all_predictions),
            "high_risk_count": risk_counts.get('HIGH', 0) + risk_counts.get('CRITICAL', 0)
        }


# ============================================================================
# Factory function for dependency injection
# ============================================================================


def get_prediction_service(db: Session, model_path: str = 'backend/ml_models/burnout_model.pkl') -> PredictionService:
    """
    Factory function for creating prediction service using a database session.
    """
    # 1. Repositories
    prediction_repo = AgentPredictionRepository(db)
    daily_log_repo = DailyLogRepository(db)
    employee_repo = EmployeeRepository(db)
    
    # 2. Queue Service
    queue_service = DailyLogQueueService(db)
    
    # 3. Predictor
    predictor = BurnoutPredictor(daily_log_repo, employee_repo)
    
    # 4. Service
    return PredictionService(
        predictor=predictor,
        prediction_repository=prediction_repo,
        daily_log_repository=daily_log_repo,
        employee_repository=employee_repo,
        queue_service=queue_service,
        model_path=model_path
    )
