
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from backend.infrastructure.persistence.database import SessionLocal, init_db
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from backend.infrastructure.persistence.repositories.model_version_repository import ModelVersionRepository
from backend.infrastructure.persistence.repositories.system_settings_repository import SystemSettingsRepository
from backend.application.services.dataset_formatter_service import DatasetFormatterService
from backend.application.services.training_service import ModelTrainingService
from backend.application.services.model_registry import ModelRegistry
from backend.ML.burnout_predictor import BurnoutPredictor
from backend.domain.entities.model_version import ModelVersionEntity
from backend.domain.enums.enums import TrainingMode

def run_manual_training():
    print("🚀 Starting Manual Training Test...")
    print("=" * 60)

    # 1. Setup DB
    init_db()
    db = SessionLocal()

    try:
        # 2. Setup Repositories
        pred_repo = AgentPredictionRepository(db)
        log_repo = DailyLogRepository(db)
        employee_repo = EmployeeRepository(db)
        version_repo = ModelVersionRepository(db)
        settings_repo = SystemSettingsRepository(db)

        # 3. Setup Services
        formatter = DatasetFormatterService(pred_repo, log_repo)
        
        predictor = BurnoutPredictor(daily_log_repo=log_repo, employee_repo=employee_repo)
        
        # We need dependencies for Training Service
        trainer = ModelTrainingService(
            predictor=predictor,
            daily_log_repository=log_repo
        )

        settings = settings_repo.get_settings()
        print(f"📊 Current System State: {settings.new_samples_count} new samples")

        # 4. Generate Dataset
        dataset_path = "backend/data/employee_burnout_form_data_final.csv" # Default fallback
        print("\n📂 Step 1: Generating Dataset...")
        try:
            # Try to generate from DB validations
            # We force it to look for *any* validations since beginning
            paths = formatter.generate_dataset(since=datetime.min)
            dataset_path = paths['train_file']
            print(f"   ✅ Generated new dataset from DB: {dataset_path}")
        except Exception as e:
            print(f"   ⚠️ Could not generate dataset from DB ({e})")
            print(f"   🔄 Falling back to static dataset: {dataset_path}")

        # 5. Run Training
        print("\n🏋️ Step 2: Running Training...")
        try:
            result = trainer.retrain(
                mode=TrainingMode.FULL,
                dataset_reference=dataset_path,
                settings=settings
            )

            if result['success']:
                print(f"   ✅ Training Successful!")
                print(f"   Model Version: {result['model_version']}")
                print(f"   R2 Score: {result['metrics']['test_r2_score']:.4f}")
                
                 # 6. Save Version
                print("\n💾 Step 3: Saving Version History...")
                new_version = ModelVersionEntity(
                    version_number=result["model_version"],
                    training_mode="MANUAL",
                    dataset_size=result["metrics"]["train_samples"],
                    model_file_path=result["model_path"],
                    accuracy=result["metrics"].get("test_r2_score"),
                    created_at=datetime.utcnow()
                )
                version_repo.add(new_version)
                print(f"   ✅ Version {new_version.version_number} persisted to DB.")

                # 7. Hot Swap
                print("\n🔥 Step 4: Testing Hot-Swap...")
                registry = ModelRegistry()
                if not registry.active_model:
                     print("   (Registry was empty, loading initial model first for demo...)")
                     # Just to simulate a swap, we need an old one. 
                     # But actually registry might be empty in this script process since it's separate from main API process.
                     # This is isolated process, so we just prove we CAN load it.
                     pass
                
                # Load new model into predictor
                predictor.load_model(result["model_path"])
                registry.load_new_model(predictor)
                print(f"   ✅ Model loaded into Registry. Active model: {registry.active_model}")

            else:
                print(f"   ❌ Training Failed: {result['error']}")

        except Exception as e:
             print(f"   ❌ Training crashed: {e}")
             import traceback
             traceback.print_exc()

    finally:
        db.close()
        print("\n🏁 Test Complete.")

if __name__ == "__main__":
    run_manual_training()
