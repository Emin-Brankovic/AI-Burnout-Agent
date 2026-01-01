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
from backend.infrastructure.persistence.repositories import daily_log_repository
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository


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
        """
        Predict burnout for a single daily log and optionally save to database.

        Args:
            daily_log: DailyLogEntity to predict
            save_to_db: Whether to save prediction to database (default: True)

        Returns:
            AgentPredictionEntity with prediction results

        Raises:
            RuntimeError: If model not loaded
        """
        if not self.predictor.is_model_loaded:
            raise RuntimeError("Model not loaded. Cannot make predictions.")

        print(f"🔮 Predicting burnout for Employee {daily_log.employee_id} (Log ID: {daily_log.id})")

        # Make prediction using BurnoutPredictor
        prediction_result: PredictionResult = self.predictor.predict(daily_log)

        # save_temp_daily_log = DailyLogEntity(
        #     id=None,
        #     employee_id=request.employee_id,
        #     log_date=request.log_date or datetime.now(),
        #     hours_worked=request.hours_worked,
        #     hours_slept=request.hours_slept,
        #     daily_personal_time=request.daily_personal_time,
        #     motivation_level=request.motivation_level,
        #     stress_level=request.stress_level,
        #     workload_intensity=request.workload_intensity,
        #     overtime_hours_today=request.overtime_hours_today,
        #     status='pending',  # ✅ Add this
        #     processed_at=datetime.now(),  # ✅ Add this (required by database)
        #     reviewed_at=None  # ✅ Add this
        # )

        daily_log.status=DailyLogStatus.ANALYZED
        daily_log.processed_at=datetime.now()
        daily_log.reviewed_at = None

          # Create instance with db session
        self.daily_log_repository.add(daily_log)

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
        """
        Convert PredictionResult to AgentPredictionEntity.

        Args:
            daily_log: Source daily log
            prediction_result: Prediction result from BurnoutPredictor

        Returns:
            AgentPredictionEntity ready for persistence
        """
        entity = AgentPredictionEntity(
            daily_log_id=daily_log.id,
            prediction_type='BURNOUT_RISK',
            prediction_value=str(prediction_result.burnout_rate),
            confidence_score=prediction_result.confidence,
            created_at=datetime.utcnow()
        )

        # Add risk_level and message as attributes afterward
        entity.risk_level = prediction_result.risk_level
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

    def get_predictions_by_risk_level(self, risk_level: str) -> List[AgentPredictionEntity]:
        """
        Get all predictions with specific risk level.

        Args:
            risk_level: Risk level (NORMAL, MEDIUM, HIGH, CRITICAL)

        Returns:
            List of predictions with that risk level
        """
        all_predictions = self.prediction_repository.get_all()

        return [
            p for p in all_predictions
            if p.risk_level == risk_level
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
            risk_level = prediction.risk_level or 'UNKNOWN'
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
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

def get_prediction_service(
        prediction_repository: AgentPredictionRepositoryInterface,
        daily_log_repository: DailyLogRepositoryInterface,
        employee_repository: EmployeeRepositoryInterface,
        model_path: str = 'backend/ml_models/burnout_model.pkl'

) -> PredictionService:
    """
    Factory function for creating prediction service.

    Args:
        prediction_repository: Repository for storing predictions
        model_path: Path to trained model

    Returns:
        PredictionService instance
    """
    predictor = BurnoutPredictor(daily_log_repository,employee_repository)

    return PredictionService(
        predictor=predictor,
        prediction_repository=prediction_repository,
        model_path=model_path,
        daily_log_repository=daily_log_repository,
        employee_repository=employee_repository

    )
