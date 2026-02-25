from datetime import datetime
from typing import List, Optional
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.enums.enums import DailyLogStatus, BurnoutRiskLevel
from backend.domain.repositories_interfaces.agent_prediction_repository_interface import \
    AgentPredictionRepositoryInterface
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.domain.repositories_interfaces.employee_repository_interface import EmployeeRepositoryInterface
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from backend.infrastructure.persistence.repositories.system_settings_repository import SystemSettingsRepository
from backend.application.helpers.agent_policy_helper import AgentPolicyHelper
from backend.application.services.email_notification_service import EmailNotificationService
from backend.application.services.email_service import EmailService, EmailConfig
from sqlalchemy.orm import Session


class ReviewService:
    def __init__(
            self,
            prediction_repository: AgentPredictionRepositoryInterface,
            daily_log_repository: DailyLogRepositoryInterface,
            employee_repository: EmployeeRepositoryInterface,
            policy_helper,
            notification_service,
            settings_repository: SystemSettingsRepository  # Added dependency
    ):
        self.prediction_repo = prediction_repository
        self.log_repo = daily_log_repository
        self.employee_repo = employee_repository
        self.policy_helper = policy_helper
        self.notification_service = notification_service
        self.settings_repo = settings_repository

    # ========== RETRIEVAL METHODS ==========

    def get_pending_reviews(self) -> List[AgentPredictionEntity]:
        """Fetch all predictions that require HR attention."""
        return self.prediction_repo.get_pending_reviews()

    def get_review_details(self, prediction_id: int) -> dict:
        """Get full context for HR to make an informed decision."""
        prediction = self.prediction_repo.get_by_id(prediction_id)
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found.")

        daily_log = self.log_repo.get_by_id(prediction.daily_log_id)

        return {
            "prediction": prediction,
            "log_data": daily_log,
            "confidence_score": prediction.confidence_score,
            "ai_prediction_type": prediction.burnout_risk
        }

    # ========== VALIDATION METHODS ==========

    async def submit_review(
            self,
            prediction_id: int,
            is_correct: bool,
            hr_notes: Optional[str] = None,
            hr_burnout_rate: Optional[float] = None
    ) -> AgentPredictionEntity:
        """
        Process HR feedback on a specific prediction.

        Args:
            prediction_id: ID of the prediction to review
            is_correct: Whether the AI prediction was correct
            hr_notes: Optional notes from the HR reviewer
            hr_burnout_rate: Optional HR-corrected burnout rate (0.0-1.0).
                             When provided, this becomes the gold label for retraining.
                             When not provided but is_correct=True, uses the model's original burnout_rate.
        """
        # 1. Fetch prediction and associated entities
        prediction = self.prediction_repo.get_by_id(prediction_id)
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found.")

        daily_log = self.log_repo.get_by_id(prediction.daily_log_id)
        employee = self.employee_repo.get_by_id(daily_log.employee_id)

        if not employee:
            raise ValueError(f"Employee for log {daily_log.id} not found.")

        # 2. Update Prediction Ground Truth (Mental 'Learn' Phase)
        # human_validation stores the HR-corrected burnout rate (gold label)
        if hr_burnout_rate is not None:
            # HR explicitly provided a corrected burnout rate
            prediction.human_validation = round(float(hr_burnout_rate), 4)
        elif is_correct:
            # HR confirmed the model prediction is correct → use model's own rate as gold label
            prediction.human_validation = prediction.burnout_rate
        else:
            # HR says prediction is wrong but didn't provide a corrected value
            # Leave human_validation as None so this sample is skipped during training
            prediction.human_validation = None

        prediction.needs_review = False
        prediction.review_notes = hr_notes
        prediction.reviewed_at = datetime.utcnow()

        # Log which model version produced this prediction (for before/after tracking)
        if not prediction.model_version:
            from backend.application.services.model_registry import ModelRegistry
            registry = ModelRegistry()
            prediction.model_version = registry.current_version or "unknown"

        # 3. Update Daily Log status
        daily_log.status = DailyLogStatus.REVIEWED
        daily_log.processed_at = datetime.utcnow()

        # 4. Handle Defered "Act" Logic
        if is_correct:
            prediction_type = prediction.burnout_risk

            # CASE A: HIGH RISK
            if prediction_type == BurnoutRiskLevel.HIGH:
                employee.high_burnout_streak += 1
                current_streak = employee.high_burnout_streak

                if self.policy_helper.should_send_critical_alert(current_streak):
                    recent_history = self.policy_helper.get_recent_history(employee.id, days=current_streak)

                    await self.notification_service.send_critical_alert(
                        employee_id=employee.id,
                        employee_name=f"Employee {employee.id}",
                        current_prediction=prediction,
                        recent_predictions=recent_history,
                        streak=current_streak,
                        log_date=daily_log.log_date
                    )
                    employee.last_alert_sent = datetime.utcnow()

            # CASE B: CRITICAL RISK
            elif prediction_type == BurnoutRiskLevel.CRITICAL:
                await self.notification_service.send_critical_alert(
                    employee_id=employee.id,
                    employee_name=f"Employee {employee.id}",
                    current_prediction=prediction,
                    recent_predictions=[],
                    streak=1,
                    log_date=daily_log.log_date
                )
                employee.last_alert_sent = datetime.utcnow()

            # CASE C: RECOVERY
            else:
                if employee.high_burnout_streak > 0:
                    employee.high_burnout_streak = 0
                    print(f"✅ Recovery confirmed. Streak reset for Employee {employee.id}")

        else:
            print(f"❌ HR marked prediction as FALSE. Data preserved for training.")

        # 5. Persist all changes
        self.employee_repo.update(employee)
        self.log_repo.update(daily_log)
        
        
        return self.prediction_repo.update(prediction)

    # ========== DATA PREP FOR LEARNING ==========

    def get_training_corrections(self, since: datetime) -> List[AgentPredictionEntity]:
        """
        Fetch samples where AI was wrong or right to retrain the Ridge model.
        """
        return self.prediction_repo.get_validated_since(since)


from backend.application.services.email_service import get_email_service, get_email_notification_service


def get_notification_service() -> EmailNotificationService:
    """Helper to maintain backward compatibility in review_service.py."""
    return get_email_notification_service()


def get_review_service(db: Session) -> ReviewService:
    """
    Factory function for creating ReviewService.
    """
    prediction_repository = AgentPredictionRepository(db)
    daily_log_repository = DailyLogRepository(db)
    employee_repository = EmployeeRepository(db)
    settings_repository = SystemSettingsRepository(db)

    policy_helper = AgentPolicyHelper(
        daily_log_repository=daily_log_repository,
        prediction_repository=prediction_repository
    )

    notification_service = get_notification_service()

    return ReviewService(
        prediction_repository=prediction_repository,
        daily_log_repository=daily_log_repository,
        employee_repository=employee_repository,
        policy_helper=policy_helper,
        notification_service=notification_service,
        settings_repository=settings_repository
    )
