"""
Model Training Service

Orchestrates the complete ML model training pipeline:
- Data loading and splitting
- Model training
- Model evaluation
- Model versioning and persistence
"""

from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

import joblib
import pandas as pd
import json
from sklearn.model_selection import train_test_split

from backend.ML.burnout_predictor import (
    BurnoutPredictor,
    TrainingSample,
    EvaluationMetrics
)
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepositoryInterface
from backend.domain.entities.daily_log import DailyLogEntity
from backend.infrastructure.persistence.database import SessionLocal
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository

from backend.domain.interfaces.trainer_interface import ITrainer
from backend.domain.enums.enums import TrainingMode
from backend.domain.entities.system_settings import SystemSettingsEntity

class ModelTrainingService(ITrainer):
    """
    Service for training and evaluating burnout prediction models.
    Implements ITrainer to plug into the Learning Worker.
    """

    def __init__(
            self,
            predictor: BurnoutPredictor,
            daily_log_repository: Optional[DailyLogRepositoryInterface] = None,
            data_path: str = 'backend/data/employee_burnout_form_data_final.csv',
            models_dir: str = 'backend/ml_models'
    ):
        """
        Initialize training service.
        """
        self.predictor = predictor
        self.repository = daily_log_repository
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    # ========== DATA LOADING ==========

    def load_samples_from_csv(self) -> List[TrainingSample]:
        """
        Load training samples from CSV file.

        Returns:
            List of TrainingSample instances

        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Training data not found: {self.data_path}")

        df = pd.read_csv(self.data_path)
        samples = []

        print(f"📂 Loading data from {self.data_path}")
        print(f"   Rows: {len(df)}")
        print(f"   Unique employees: {df['Employee_ID'].nunique()}")

        for _, row in df.iterrows():
            sample = TrainingSample(
                employee_id=int(row['Employee_ID']),
                work_hours_per_day=float(row['Work_Hours_Per_Day']),
                sleep_hours_per_night=float(row['Sleep_Hours_Per_Night']),
                personal_time_hours_per_day=float(row['Personal_Time_Hours_Per_Day']),
                motivation_level=int(row['Motivation_Level']),
                work_stress_level=int(row['Work_Stress_Level']),
                workload_intensity=int(row['Workload_Intensity']),
                overtime_hours_today=float(row['Overtime_Hours_Today']),
                burnout_rate=float(row['Burnout_Rate_Daily'])
            )
            samples.append(sample)

        print(f"✅ Loaded {len(samples)} training samples")
        return samples


    # ========== TRAINING & EVALUATION ==========

    async def train_model(
            self,
            model_name: str = 'burnout_model',
    ) -> Tuple[str, EvaluationMetrics]:
        """
        Train model on training samples.

        Args:
            model_name: Name for model file (without .pkl)

        Returns:
            Tuple of (model_path, training_metrics)
        """
        samples=self.load_samples_from_csv()

        model_filename = f"{model_name}.pkl"
        model_path = 'backend/ml_models/burnout_model.pkl'

        print(f"\n🔧 Training model: {model_filename}")
        print(f"   Training samples: {len(samples)}")

        train_metrics = await self.predictor.train(
            training_data=samples,
        )

        print(f"\n✅ Training complete!")
        print(f"   Train R²: {train_metrics.train_r2_score:.4f}")
        print(f"   Model saved: {model_path}")

        eval_metrics = self.predictor.evaluate(validation_data=samples)

        print(f"\n✅ Evaluation complete!")
        print(f"   Validation R²: {eval_metrics.test_r2_score:.4f}")
        print(f"   MSE: {eval_metrics.mse:.4f}")
        print(f"   MAE: {eval_metrics.mae:.4f}")


        final_metrics = EvaluationMetrics(
            train_r2_score=train_metrics.train_r2_score if hasattr(train_metrics,
                                                                   'train_r2_score') else eval_metrics.test_r2_score,
            test_r2_score=eval_metrics.test_r2_score,
            train_samples=train_metrics.train_samples if hasattr(train_metrics, 'train_samples') else len(samples),
            test_samples=eval_metrics.test_samples,
            features_count=eval_metrics.features_count,
            mse=eval_metrics.mse,
            mae=eval_metrics.mae,
        )



        return str(model_path), final_metrics

    def retrain(
        self, 
        mode: TrainingMode, 
        dataset_reference: str, 
        settings: SystemSettingsEntity
    ) -> Dict[str, Any]:
        """
        Execute model retraining via ITrainer interface.
        """
        import asyncio
        
        # Update internal data path to point to the new dataset from Formatter
        self.data_path = Path(dataset_reference)
        
        # Generate version string
        version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_name = f"burnout_model_{version_id}"
        
        # Run async training synchronously
        log_message = ""
        try:
            # Reusing existing train_model logic which handles loading from self.data_path
            model_path, metrics = asyncio.run(self.train_model(model_name=model_name))
            
            return {
                "success": True,
                "model_version": version_id,
                "model_path": model_path,
                "metrics": {
                    "train_r2_score": metrics.train_r2_score,
                    "test_r2_score": metrics.test_r2_score,
                    "train_samples": metrics.train_samples
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    #         self,
    # ) -> EvaluationMetrics:
    #     """
    #     Evaluate trained model on validation data.
    #
    #     Args:
    #         validation_samples: Validation data
    #
    #     Returns:
    #         EvaluationMetrics with validation results
    #     """
    #     samples = self.load_samples_from_csv()
    #
    #     print(f"\n📈 Evaluating model on validation set...")
    #     print(f"   Validation samples: {len(samples)}")
    #
    #     eval_metrics = self.predictor.evaluate(validation_data=samples)
    #
    #     print(f"\n✅ Evaluation complete!")
    #     print(f"   Validation R²: {eval_metrics.test_r2_score:.4f}")
    #     print(f"   MSE: {eval_metrics.mse:.4f}")
    #     print(f"   MAE: {eval_metrics.mae:.4f}")
    #
    #     return eval_metrics

    # ========== FULL PIPELINE ==========



# ============================================================================
# Factory function for dependency injection
# ============================================================================

def get_training_service(
        daily_log_repository: Optional[DailyLogRepositoryInterface] = None
) -> ModelTrainingService:
    """
    Factory function for creating training service.

    Args:
        daily_log_repository: Optional repository for loading data from DB

    Returns:
        ModelTrainingService instance
    """

    db_session = SessionLocal()

    daily_log_repository = DailyLogRepository(db_session)

    employee_repository = EmployeeRepository(db_session)

    # Initialize BurnoutPredictor with repository dependencies
    predictor = BurnoutPredictor(
        daily_log_repo=daily_log_repository,
        employee_repo=employee_repository
    )

    return ModelTrainingService(
        predictor=predictor,
        daily_log_repository=daily_log_repository
    )
