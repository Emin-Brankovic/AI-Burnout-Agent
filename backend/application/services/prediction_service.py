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

from sqlalchemy.orm import Session

from backend.ML.burnout_predictor import BurnoutPredictor, PredictionResult
from backend.application.services.queue_service import DailyLogQueueService
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
from backend.application.services.model_registry import ModelRegistry
from backend.infrastructure.persistence.repositories.system_settings_repository import SystemSettingsRepository

class PredictionService:
    """
    Service for making burnout predictions and persisting results.
    Supports automatic model hot-swapping with version tracking.
    """

    def __init__(
            self,
            predictor: BurnoutPredictor,
            prediction_repository: AgentPredictionRepositoryInterface,
            daily_log_repository: DailyLogRepositoryInterface,
            employee_repository: EmployeeRepositoryInterface,
            queue_service: Optional[DailyLogQueueService] = None,
            model_path: str = 'backend/ml_models/burnout_model.pkl',
            settings_repository: Optional[SystemSettingsRepository] = None
    ):
        self.predictor = predictor
        self.prediction_repository = prediction_repository
        self.model_path = Path(model_path)
        self.daily_log_repository = daily_log_repository
        self.employee_repository = employee_repository
        self.queue_service = queue_service
        self.registry = ModelRegistry()
        self.settings_repo = settings_repository

        # Configure model factory for automatic hot-swapping
        self._setup_model_factory()

        # Auto-load model if it exists and registry is empty
        if self.model_path.exists() and not self.registry.active_model:
            print(f"✅ Loading initial model from {self.model_path}")
            self.predictor.load_model(str(self.model_path))
            # Load with version tracking
            self.registry.load_new_model(
                self.predictor, 
                model_path=str(self.model_path)
            )
        elif not self.model_path.exists():
            print(f"⚠️ Model not found at {self.model_path}. Training initial model...")
            self._train_initial_model()

    def _setup_model_factory(self):
        """Configure the model factory for hot-swapping."""
        def create_predictor():
            """Factory function to create new predictor instances."""
            return BurnoutPredictor(
                daily_log_repo=self.daily_log_repository,
                employee_repo=self.employee_repository
            )
        
        self.registry.set_model_factory(create_predictor)

    def _train_initial_model(self):
        """
        Train an initial model when no model file exists.
        This ensures the system can start even without a pre-trained model.
        Note: This is a fallback - main.py should handle initial training in async context.
        """
        import asyncio
        from backend.application.services.training_service import ModelTrainingService
        
        try:
            # Create a training service instance
            training_service = ModelTrainingService(
                predictor=self.predictor,
                daily_log_repository=self.daily_log_repository
            )
            
            # Handle both cases: running inside event loop or not
            try:
                loop = asyncio.get_running_loop()
                # We're inside an event loop - create a task and use nest_asyncio or skip
                # Since we can't easily await here, just log and let main.py handle it
                print("   ⚠️ Skipping training in PredictionService (will be handled by main.py)")
                return
            except RuntimeError:
                # No running event loop - safe to use asyncio.run()
                model_path, metrics = asyncio.run(
                    training_service.train_model(model_name='burnout_model', isRetrain=False)
                )
            
            print(f"✅ Initial model trained successfully!")
            print(f"   Model saved to: {model_path}")
            print(f"   Train R²: {metrics.train_r2_score:.4f}")
            print(f"   Test R²: {metrics.test_r2_score:.4f}")
            
            # Load the newly trained model into registry
            self.predictor.load_model(str(self.model_path))
            self.registry.load_new_model(
                self.predictor,
                model_path=str(self.model_path)
            )
            
        except Exception as e:
            print(f"❌ Failed to train initial model: {e}")
            import traceback
            traceback.print_exc()

    # ========== PREDICTION METHODS ==========

    def predict_for_daily_log(
            self,
            daily_log: DailyLogEntity,
            save_to_db: bool = True
    ) -> AgentPredictionEntity:
        
        # Use Registry for atomic thread-safe prediction with version tracking
        # This allows the background worker to hot-swap the model underneath
        prediction_result, model_version = self.registry.predict(daily_log)

        # Convert to domain entity with model version
        prediction_entity = self._convert_result_to_entity(
            daily_log=daily_log,
            prediction_result=prediction_result,
            model_version=model_version
        )

        # Save to database if requested
        saved_prediction = self.prediction_repository.add(prediction_entity)


        if self.settings_repo:
             # Only increment if it's NOT flagged for review? Or counts as throughput?
             # Let's assume throughput for now as the user expects "system settings samples" to move.
             try:
                self.settings_repo.increment_samples(1)
             except Exception as e:
                print(f"⚠️ Failed to increment system settings samples: {e}")

        print(f"✅ Prediction saved via Registry (ID: {saved_prediction.id}, Model: {model_version})")
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
            prediction_result: PredictionResult,
            model_version: Optional[str] = None
    ) -> AgentPredictionEntity:
        
        entity = AgentPredictionEntity(
            daily_log_id=daily_log.id,
            burnout_risk=prediction_result.burnout_risk,  # Use from result
            burnout_rate=round(prediction_result.burnout_rate,4),  # Store float
            confidence_score=prediction_result.confidence_score,  # Renamed field
            created_at=datetime.utcnow(),
            model_version=model_version  # Track which model made this prediction
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

    def get_predictions_by_type(self, burnout_risk: str) -> List[AgentPredictionEntity]:
        """
        Get all predictions with specific type.

        Args:
            burnout_risk: Prediction risk type (NORMAL, MEDIUM, HIGH, CRITICAL)

        Returns:
            List of predictions with that type
        """
        return self.prediction_repository.get_by_type(burnout_risk)

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
            burnout_risk = prediction.burnout_risk or 'UNKNOWN'
            risk_counts[burnout_risk] = risk_counts.get(burnout_risk, 0) + 1
            total_burnout_rate += prediction.burnout_rate or 0.0

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
    settings_repo = SystemSettingsRepository(db)
    
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
        model_path=model_path,
        settings_repository=settings_repo
    )
