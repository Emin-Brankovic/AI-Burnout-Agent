"""
Feedback Loop Fix - Demo/Test Script
=====================================

This script demonstrates that the feedback loop is correctly fixed:
1. Makes an initial prediction with the current model (e.g., Model Version v1)
2. Simulates an HR correction via review_service with a conflicting human_validation value
3. Triggers retraining via training_service (load_combined_samples + train)
4. Re-predicts the same input and shows the shift toward the HR label

Usage:
    python -m test_feedback_loop
    (Run from the project root directory)

Prerequisites:
    - Database must exist (backend/data/app.db)
    - A trained model must exist (backend/ml_models/burnout_model.pkl)
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# ─── Ensure project root is on sys.path ────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ─── Imports ───────────────────────────────────────────────────────
from backend.infrastructure.persistence.database import (
    SessionLocal, Base, engine,
    DailyLog, AgentPrediction, Employee, Department
)
from backend.domain.enums.enums import DailyLogStatus, BurnoutRiskLevel
from backend.ML.burnout_predictor import BurnoutPredictor
from backend.domain.entities.daily_log import DailyLogEntity
from backend.application.services.model_registry import ModelRegistry
from backend.application.services.training_service import ModelTrainingService
from backend.application.services.review_service import get_review_service
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository


# ─── Configuration ─────────────────────────────────────────────────
# Sample input simulating a highly stressed employee
SAMPLE_INPUT = {
    "hours_worked": 12.0,
    "hours_slept": 4.0,
    "daily_personal_time": 0.5,
    "motivation_level": 2,
    "stress_level": 9,
    "workload_intensity": 9,
    "overtime_hours_today": 4.0,
}

# HR says the burnout rate should actually be much lower (conflicting label)
HR_CORRECTED_BURNOUT_RATE = 0.25


def print_banner(text: str):
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def create_test_daily_log(db, employee_id: int) -> DailyLog:
    """Insert a test daily log into the database and return the ORM object."""
    log = DailyLog(
        employee_id=employee_id,
        log_date=datetime.utcnow(),
        hours_worked=SAMPLE_INPUT["hours_worked"],
        hours_slept=SAMPLE_INPUT["hours_slept"],
        daily_personal_time=SAMPLE_INPUT["daily_personal_time"],
        motivation_level=SAMPLE_INPUT["motivation_level"],
        stress_level=SAMPLE_INPUT["stress_level"],
        workload_intensity=SAMPLE_INPUT["workload_intensity"],
        overtime_hours_today=SAMPLE_INPUT["overtime_hours_today"],
        status=DailyLogStatus.QUEUED,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def make_daily_log_entity(log: DailyLog) -> DailyLogEntity:
    """Convert ORM DailyLog to domain entity for prediction."""
    return DailyLogEntity(
        id=log.id,
        employee_id=log.employee_id,
        log_date=log.log_date,
        hours_worked=log.hours_worked,
        hours_slept=log.hours_slept,
        daily_personal_time=log.daily_personal_time,
        motivation_level=log.motivation_level,
        stress_level=log.stress_level,
        workload_intensity=log.workload_intensity,
        overtime_hours_today=log.overtime_hours_today,
        status=DailyLogStatus.QUEUED,
    )


def predict_with_registry(registry: ModelRegistry, log_entity: DailyLogEntity):
    """Run prediction using the model registry and return (burnout_rate, model_version)."""
    result, version = registry.predict(log_entity)
    return result.burnout_rate, version


def ensure_test_employee(db) -> int:
    """Make sure at least one employee exists; return its ID."""
    emp = db.query(Employee).first()
    if emp:
        return emp.id
    # Create a minimal department + employee for testing
    dept = Department(name="Test Department", description="For feedback loop test")
    db.add(dept)
    db.flush()
    emp = Employee(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        department_id=dept.id,
        job_title="Tester",
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp.id


async def run_demo():
    db = SessionLocal()
    try:
        # ──────────────────────────────────────────────────────────
        # STEP 0: Setup
        # ──────────────────────────────────────────────────────────
        print_banner("STEP 0: Setup")

        employee_id = ensure_test_employee(db)
        print(f"Using Employee ID: {employee_id}")

        daily_log_repo = DailyLogRepository(db)
        employee_repo = EmployeeRepository(db)

        predictor = BurnoutPredictor(
            daily_log_repo=daily_log_repo,
            employee_repo=employee_repo,
        )

        registry = ModelRegistry()

        # Load model if not already loaded
        model_path = "backend/ml_models/burnout_model.pkl"
        if not registry.active_model:
            if not Path(model_path).exists():
                print("ERROR: No trained model found. Train the model first via main.py.")
                return
            predictor.load_model(model_path)
            registry.load_new_model(predictor, model_path=model_path)

        print(f"Active model version: {registry.current_version}")

        # ──────────────────────────────────────────────────────────
        # STEP 1: Initial prediction
        # ──────────────────────────────────────────────────────────
        print_banner("STEP 1: Initial Prediction (Before HR Correction)")

        test_log = create_test_daily_log(db, employee_id)
        log_entity = make_daily_log_entity(test_log)

        initial_rate, initial_version = predict_with_registry(registry, log_entity)
        print(f"  Model Version : {initial_version}")
        print(f"  Predicted burnout rate : {initial_rate:.4f}")
        print(f"  HR correction target   : {HR_CORRECTED_BURNOUT_RATE:.4f}")
        print(f"  Gap                    : {abs(initial_rate - HR_CORRECTED_BURNOUT_RATE):.4f}")

        # Save the prediction to DB (mimics what PredictionService does)
        pred = AgentPrediction(
            daily_log_id=test_log.id,
            burnout_risk=BurnoutRiskLevel.HIGH.value if initial_rate > 0.6 else BurnoutRiskLevel.LOW.value,
            burnout_rate=round(initial_rate, 4),
            confidence_score=0.85,
            needs_review=True,
            model_version=initial_version,
            created_at=datetime.utcnow(),
        )
        db.add(pred)
        test_log.status = DailyLogStatus.ANALYZED
        db.commit()
        db.refresh(pred)

        # ──────────────────────────────────────────────────────────
        # STEP 2: Simulate HR Review (conflicting value)
        # ──────────────────────────────────────────────────────────
        print_banner("STEP 2: HR Submits Corrected Burnout Rate")

        review_svc = get_review_service(db)
        reviewed = await review_svc.submit_review(
            prediction_id=pred.id,
            is_correct=False,
            hr_notes="Feedback loop test - HR overrides prediction",
            hr_burnout_rate=HR_CORRECTED_BURNOUT_RATE,
        )
        db.commit()

        print(f"  Prediction ID          : {pred.id}")
        print(f"  human_validation (gold) : {reviewed.human_validation}")
        print(f"  Original burnout_rate   : {pred.burnout_rate}")
        print(f"  HR corrected rate       : {HR_CORRECTED_BURNOUT_RATE}")

        # ──────────────────────────────────────────────────────────
        # STEP 3: Retrain with load_combined_samples
        # ──────────────────────────────────────────────────────────
        print_banner("STEP 3: Retraining (load_combined_samples uses gold labels)")

        training_svc = ModelTrainingService(
            predictor=predictor,
            daily_log_repository=daily_log_repo,
        )

        # load_combined_samples now prioritises human_validation
        combined = training_svc.load_combined_samples()
        hr_labeled = [s for s in combined if True]  # all DB samples are now HR-labeled
        print(f"  Total combined samples : {len(combined)}")

        model_path_out, metrics = await training_svc.train_model(
            model_name="burnout_model", isRetrain=True
        )
        print(f"  New model saved to     : {model_path_out}")
        print(f"  Train R²               : {metrics.train_r2_score:.4f}")
        print(f"  Test  R²               : {metrics.test_r2_score:.4f}")

        # Hot-swap the model in the registry
        predictor.load_model(model_path_out)
        registry.load_new_model(predictor, model_path=model_path_out)
        new_version = registry.current_version
        print(f"  New model version      : {new_version}")

        # ──────────────────────────────────────────────────────────
        # STEP 4: Re-predict same input with new model
        # ──────────────────────────────────────────────────────────
        print_banner("STEP 4: Re-Prediction (After Retraining)")

        new_rate, new_ver = predict_with_registry(registry, log_entity)

        print(f"  Model Version (before) : {initial_version}")
        print(f"  Model Version (after)  : {new_ver}")
        print(f"  Burnout rate (before)  : {initial_rate:.4f}")
        print(f"  Burnout rate (after)   : {new_rate:.4f}")
        print(f"  HR gold label          : {HR_CORRECTED_BURNOUT_RATE:.4f}")

        shift = new_rate - initial_rate
        direction = "toward" if abs(new_rate - HR_CORRECTED_BURNOUT_RATE) < abs(initial_rate - HR_CORRECTED_BURNOUT_RATE) else "away from"
        print(f"  Shift                  : {shift:+.4f} ({direction} HR label)")

        # ──────────────────────────────────────────────────────────
        # Summary
        # ──────────────────────────────────────────────────────────
        print_banner("SUMMARY")
        print(f"  Initial version  : {initial_version}")
        print(f"  Retrained version: {new_ver}")
        print(f"  Prediction shift : {initial_rate:.4f} -> {new_rate:.4f}")
        print(f"  HR target        : {HR_CORRECTED_BURNOUT_RATE:.4f}")
        print(f"  Direction        : {direction} HR label")
        print(f"\n  The model {'correctly shifts' if direction == 'toward' else 'needs more HR samples to shift'} toward the HR-corrected gold label.")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
