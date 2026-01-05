from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

from backend.application.services.email_notification_service import EmailNotificationService
from backend.core.software_agent import SoftwareAgent
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.enums.enums import DailyLogStatus, BurnoutRiskLevel
from backend.application.services.queue_service import DailyLogQueueService
from backend.application.services.prediction_service import PredictionService
from backend.application.helpers.agent_policy_helper import AgentPolicyHelper
@dataclass
class PredictionResult:
    """
    Result of one agent tick.

    This is returned to the Web layer for real-time updates.
    """
    daily_log_id: int
    employee_id: int
    burnout_rate: float
    prediction_type: str
    confidence_score: float
    needs_review: bool
    processed_at: datetime
    message: str

class BurnoutPredictionAgentRunner(SoftwareAgent[DailyLogEntity, AgentPredictionEntity, PredictionResult]):

    def __init__(
            self,
            queue_service: DailyLogQueueService,
            prediction_service: PredictionService,
            email_notification_service: EmailNotificationService,
            name: str = "BurnoutPredictionAgent"
    ):
        super().__init__(name=name)
        self._queue = queue_service
        self._predictor = prediction_service
        self._notification = email_notification_service
        self._current_log: Optional[DailyLogEntity] = None

        # Tracking
        self._prediction_history: Dict[int, List[Dict]] = {}

        # Config
        self.CRITICAL_STREAK_THRESHOLD = 3
        self.MIN_DAYS_BETWEEN_ALERTS = 7
        self.CONFIDENCE_THRESHOLD = 0.70  # Predictions below this confidence need review

        self.policy_helper = AgentPolicyHelper(
            daily_log_repository=prediction_service.daily_log_repository,
            prediction_repository=prediction_service.prediction_repository,
            confidence_threshold=0.70
        )

        # ========================================
    # SENSE - Observe environment
    # ========================================

    async def sense(self) -> Optional[DailyLogEntity]:
        # Check if there are pending logs
        queue_size = await self._queue.get_queue_size(DailyLogStatus.QUEUED)

        if queue_size == 0:
            # No work - agent idles
            return None

        # Dequeue next daily log (returns DailyLog model from database)
        daily_log_model = await self._queue.dequeue_next(DailyLogStatus.QUEUED)

        if daily_log_model is None:
            return None

        # Convert database model to domain entity
        # Note: Your queue service returns DailyLog model, not entity
        # So we need to convert it here or in the service
        from backend.infrastructure.persistence.data_mappers import daily_log_model_to_entity
        daily_log = daily_log_model_to_entity(daily_log_model)

        # SAVE in context for think/act phases
        self._current_log = daily_log

        # Mark as PROCESSING (agent lock)
        await self._queue.update_status(
            log_id=daily_log.id,
            new_status=DailyLogStatus.PROCESSING,
            processed_at=None
        )

        print(f"👁️  SENSE: DailyLog {daily_log.id} (Employee {daily_log.employee_id})")

        return daily_log

    # ========================================
    # THINK - Make decision
    # ========================================

    async def think(self, daily_log: DailyLogEntity) -> AgentPredictionEntity:

        # Predict burnout using prediction service
        prediction = self._predictor.predict_for_daily_log(daily_log)

        # Apply business rules to determine if review is needed
        needs_review = self.policy_helper.should_require_review(prediction)

        # Set appropriate status based on review requirement
        if needs_review:
            # Low confidence or high risk - needs human review
            self._current_log.status= DailyLogStatus.PENDING_REVIEW
            prediction.needs_review=needs_review
        else:
            # High confidence - automatic classification
            self._current_log.status = DailyLogStatus.ANALYZED
            prediction.needs_review=needs_review

        if prediction.id:
            updated_prediction = self._predictor.prediction_repository.update(prediction)
            print(f"✅ Updated prediction {updated_prediction.id} with needs_review={needs_review}")

        return prediction

    # ========================================
    # ACT - Execute action
    # ========================================

    async def act(self, prediction: AgentPredictionEntity) -> PredictionResult:
        """ACT sa email notifikacijama"""

        if not self._current_log:
            raise RuntimeError("No current daily log in context!")

        daily_log = self._current_log
        employee_id = daily_log.employee_id
        needs_review = prediction.needs_review

        # 1. Update DB Status
        await self._queue.update_status(
            log_id=daily_log.id,
            new_status=self._current_log.status,
            processed_at=datetime.utcnow()
        )

        # 2. Handle Review Request if needed
        if self._current_log.status == DailyLogStatus.PENDING_REVIEW:
            # Email Type 2: Review request
            success = await self._notification.send_review_request(
                employee_id=employee_id,
                employee_name=f"Employee {employee_id}",
                prediction=prediction,
                log_date=daily_log.log_date
            )
            if success:
                print(f"✅ Review request sent for log {daily_log.id}")
            
            # Create result and return early for PENDING_REVIEW
            result = PredictionResult(
                daily_log_id=daily_log.id,
                employee_id=daily_log.employee_id,
                burnout_rate=prediction.burnout_rate,
                prediction_type=prediction.prediction_type,
                confidence_score=prediction.confidence_score,
                needs_review=needs_review,
                processed_at=datetime.utcnow(),
                message=prediction.message
            )
            self._current_log = None
            return result
        


        print(f"✅ ACT: DailyLog {daily_log.id} processed")
        # print(f"       Risk: {prediction.risk_level.value} ({prediction.burnout_rate:.1%})")

        # 2. ✅ POŠALJI EMAILOVE (samo 2 tipa)
        
        # Fetch employee from database
        employee = self._predictor.employee_repository.get_by_id(employee_id)
        if not employee:
            print(f"       ⚠️  Employee {employee_id} not found in database")
            employee = None
            streak = 0
            last_alert_sent = None
        else:
            streak = employee.high_burnout_streak
            last_alert_sent = employee.last_alert_sent

        # Email Type 1: CRITICAL alert - send instantly
        if prediction.prediction_type == BurnoutRiskLevel.CRITICAL:
            # Send email instantly without streak logic
            success = await self._notification.send_critical_alert(
                employee_id=employee_id,
                employee_name=f"Employee {employee_id}",
                current_prediction=prediction,
                recent_predictions=[],  # No history for instant alerts
                streak=1,  # Just indicate it's a critical alert
                log_date=daily_log.log_date
            )
            if success and employee:
                employee.last_alert_sent = datetime.utcnow()
                self._predictor.employee_repository.update(employee)
                print(f"       📧 CRITICAL alert sent instantly")
        
        # Email Type 1b: HIGH alert (sa historijom i streak logikom)
        elif prediction.prediction_type == BurnoutRiskLevel.HIGH:
            if employee:
                # Increment streak from database
                employee.high_burnout_streak = streak + 1
                streak = employee.high_burnout_streak
                self._predictor.employee_repository.update(employee)

                print(f"       ⚠️  HIGH streak: {streak} days")

                if self.policy_helper.should_send_critical_alert(employee_id, streak):
                    # ✅ Dohvati prethodne predikcije za historiju
                    recent_predictions = self.policy_helper.get_recent_history(employee_id, days=streak)

                    success = await self._notification.send_critical_alert(
                        employee_id=employee_id,
                        employee_name=f"Employee {employee_id}",
                        current_prediction=prediction,
                        recent_predictions=recent_predictions,  # ✅ Proslijedi historiju
                        streak=streak,
                        log_date=daily_log.log_date
                    )
                    if success:
                        employee.last_alert_sent = datetime.utcnow()
                        self._predictor.employee_repository.update(employee)
                        print(f"HIGH alert sent (with {len(recent_predictions)} history items)")
        else:
            # Reset streak for HIGH risk
            if employee and employee.high_burnout_streak > 0:
                old_streak = employee.high_burnout_streak
                employee.high_burnout_streak = 0
                self._predictor.employee_repository.update(employee)
                print(f"HIGH streak reset (was {old_streak})")

        # 3. Create result
        result = PredictionResult(
            daily_log_id=daily_log.id,
            employee_id=daily_log.employee_id,
            burnout_rate=prediction.burnout_rate,
            prediction_type=prediction.prediction_type,
            confidence_score=prediction.confidence_score,
            needs_review=needs_review,
            processed_at=datetime.utcnow(),
            message=prediction.message
        )

        self._current_log = None
        return result

    async def process_batch(self, batch_size: int = 10) -> List[PredictionResult]:
        """Process a batch of pending logs."""
        results = []
        for _ in range(batch_size):
            result = await self.step_async()
            if not result:
                break
            results.append(result)
        return results

    async def get_queue_stats(self) -> dict:
        """Get statistics from the queue service."""
        return await self._queue.get_queue_stats()

if __name__ == "__main__":
    print("✅ BurnoutPredictionAgentRunner loaded")
    print("   - Sense: Dequeue daily log from queue")
    print("   - Think: Predict burnout + policy")
    print("   - Act: Save prediction + update status")
