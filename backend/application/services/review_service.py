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
            policy_helper,  # Added: Needed for streak thresholds and history
            notification_service  # Added: Needed to send the deferred alerts
    ):
        self.prediction_repo = prediction_repository
        self.log_repo = daily_log_repository
        self.employee_repo = employee_repository
        self.policy_helper = policy_helper
        self.notification_service = notification_service

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
            "ai_prediction_type": prediction.prediction_type
        }

    # ========== VALIDATION METHODS ==========

    async def submit_review(
            self,
            prediction_id: int,
            is_correct: bool,
            hr_notes: Optional[str] = None
    ) -> AgentPredictionEntity:
        """
        Process HR feedback on a specific prediction.
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
        prediction.human_validation = is_correct
        prediction.needs_review = False
        prediction.review_notes = hr_notes
        prediction.reviewed_at = datetime.utcnow()

        # 3. Update Daily Log status
        daily_log.status = DailyLogStatus.REVIEWED
        daily_log.processed_at = datetime.utcnow()  # Mark when the loop finally closed

        # 4. Handle Defered "Act" Logic (The part the Runner skipped)
        if is_correct:
            prediction_type = prediction.prediction_type

            # CASE A: HIGH RISK
            if prediction_type == BurnoutRiskLevel.HIGH:
                employee.high_burnout_streak += 1
                current_streak = employee.high_burnout_streak

                # Check if we should now send the alert that was on hold
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
                    recent_predictions=[],  # Instant alert has no combined history
                    streak=1,
                    log_date=daily_log.log_date
                )
                employee.last_alert_sent = datetime.utcnow()

            # CASE C: RECOVERY (Normal/Medium)
            else:
                # If HR confirms the user is fine, we reset the streak
                if employee.high_burnout_streak > 0:
                    employee.high_burnout_streak = 0
                    print(f"✅ Recovery confirmed. Streak reset for Employee {employee.id}")

        else:
            # 5. Handle AI Mistake
            # We skip streak increments. The streak stays exactly where it was.
            print(f"❌ HR marked prediction as FALSE. Data preserved for training.")

        # 6. Persist all changes
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
        notification_service=notification_service
    )