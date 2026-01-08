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
from backend.infrastructure.persistence.database import SessionLocal, AgentPrediction
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository

from backend.domain.interfaces.trainer_interface import ITrainer
from backend.domain.enums.enums import TrainingMode
from backend.domain.entities.system_settings import SystemSettingsEntity
from backend.infrastructure.persistence.repositories.model_version_repository import ModelVersionRepository
from backend.domain.entities.model_version import ModelVersionEntity
from backend.application.services.model_registry import ModelRegistry
from backend.infrastructure.persistence.repositories.system_settings_repository import SystemSettingsRepository
from sqlalchemy.orm import Session

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

    def load_combined_samples(self) -> List[TrainingSample]:
        """
        Load training samples combining CSV data with new daily logs from database.
        
        This method:
        1. Loads original CSV data
        2. Fetches daily logs with predictions that don't need review
        3. Merges them into a combined training dataset
        
        Returns:
            List of TrainingSample instances from both CSV and database
        """
        # 1. Load original CSV samples
        csv_samples = self.load_samples_from_csv()
        
        # 2. Load new samples from database (if repository is available)
        db_samples = []
        if self.repository:
            try:
                # Import required models and mappers
                from backend.infrastructure.persistence.database import DailyLog
                from backend.domain.enums.enums import DailyLogStatus
                from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
                
                # Query logs that have predictions (analyzed status)
                analyzed_logs = (
                    self.repository.session.query(DailyLog,AgentPrediction)
                    .join(AgentPrediction, DailyLog.id == AgentPrediction.daily_log_id)  # SQL JOIN
                    .filter(DailyLog.status.in_([DailyLogStatus.ANALYZED, DailyLogStatus.REVIEWED]))
                    .all()
                )

                
                for daily_log, agent_prediction in analyzed_logs:

                    try:
                        # Convert to TrainingSample
                        sample = TrainingSample(
                            employee_id=daily_log.employee_id,
                            work_hours_per_day=daily_log.hours_worked or 8.0,
                            sleep_hours_per_night=daily_log.hours_slept or 7.0,
                            personal_time_hours_per_day=daily_log.daily_personal_time or 1.0,
                            motivation_level=daily_log.motivation_level or 5,
                            work_stress_level=daily_log.stress_level or 5,
                            workload_intensity=daily_log.workload_intensity or 5,
                            overtime_hours_today=daily_log.overtime_hours_today or 0.0,
                            burnout_rate=round(float(agent_prediction.prediction_value),2)
                        )
                        db_samples.append(sample)
                    except (ValueError, TypeError) as e:
                        print(f"   Warning: Skipping log {daily_log.id} due to conversion error: {e}")
                        continue
                
                print(f"📊 Loaded {len(db_samples)} samples from database (excluding those needing review)")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not load database samples: {e}")
                import traceback
                traceback.print_exc()
                print("   Continuing with CSV data only")
        
        # 3. Combine samples
        combined_samples = csv_samples + db_samples
        total = len(combined_samples)
        csv_count = len(csv_samples)
        db_count = len(db_samples)
        
        print(f"✅ Combined dataset: {total} samples ({csv_count} from CSV + {db_count} from DB)")
        
        return combined_samples


    # ========== TRAINING & EVALUATION ==========

    async def train_model(
            self,
            model_name: str = 'burnout_model',
            isRetrain: bool = False
    ) -> Tuple[str, EvaluationMetrics]:
        """
        Train model on training samples (CSV + database).

        Args:
            model_name: Name for model file (without .pkl)

        Returns:
            Tuple of (model_path, training_metrics)
        """
        if isRetrain:
            samples = self.load_combined_samples()
        else:
           samples = self.load_samples_from_csv()

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
            model_path, metrics = asyncio.run(self.train_model(model_name=model_name,isRetrain=True))
            
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

    async def retrain_async(
        self, 
        mode: TrainingMode, 
        dataset_reference: str, 
        settings: SystemSettingsEntity
    ) -> Dict[str, Any]:
        """
        Execute model retraining via ITrainer interface (async version).
        Use this from async contexts (e.g., FastAPI endpoints).
        """
        # Update internal data path to point to the new dataset from Formatter
        self.data_path = Path(dataset_reference)
        
        # Generate version string
        version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_name = f"burnout_model_{version_id}"
        
        try:
            # Await training directly (no asyncio.run needed)
            model_path, metrics = await self.train_model(model_name=model_name,isRetrain=True)
            
            return {
                "success": True,
                "model_version": version_id,
                "model_path": model_path,
                "metrics": {
                    "train_r2_score": metrics.train_r2_score,
                    "test_r2_score": metrics.test_r2_score,
                    "train_samples": metrics.train_samples,
                    "mse": metrics.mse,
                    "mae": metrics.mae
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_manual_training_pipeline(self, db_session: Session) -> Dict[str, Any]:
        """
        Executes the full manual training pipeline.

        Args:
            db_session: Database session for repositories

        Returns:
            Dictionary with training results
        """
        # 1. Setup Repositories
        version_repo = ModelVersionRepository(db_session)
        settings_repo = SystemSettingsRepository(db_session)

        # 2. Load Settings
        settings = settings_repo.get_settings()

        # 3. Define Dataset (Fallback for now)
        dataset_path = "backend/data/employee_burnout_form_data_final.csv"

        # 4. Run Training
        result = await self.retrain_async(
            mode=TrainingMode.FULL,
            dataset_reference=dataset_path,
            settings=settings
        )

        if result['success']:
            # 5. Save Version History
            new_version = ModelVersionEntity(
                version_number=result["model_version"],
                training_mode="MANUAL_API",
                dataset_size=result["metrics"]["train_samples"],
                model_file_path=result["model_path"],
                accuracy=result["metrics"].get("test_r2_score"),
                created_at=datetime.utcnow()
            )
            version_repo.add(new_version)
            db_session.commit()

            # 6. Hot Swap Model in Registry
            registry = ModelRegistry()
            self.predictor.load_model(result["model_path"])
            registry.load_new_model(self.predictor)

            return {
                "message": "Training pipeline completed successfully",
                "model_version": result["model_version"],
                "model_path": result["model_path"],
                "dataset_used": dataset_path,
                "metrics": result["metrics"]
            }
        else:
            raise Exception(f"Training failed: {result.get('error', 'Unknown error')}")
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
