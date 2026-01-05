"""
Agent Policy Helper for burnout management.
Handles streak logic, review requirements, and historical data retrieval.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.enums.enums import BurnoutRiskLevel


class AgentPolicyHelper:
    """Handles business rules for notifications and review flags."""

    def __init__(self, daily_log_repository, prediction_repository, confidence_threshold: float = 0.70):
        self.daily_log_repository = daily_log_repository
        self.prediction_repository = prediction_repository
        self.confidence_threshold = confidence_threshold
        self.CRITICAL_STREAK_THRESHOLD = 3

    def should_require_review(self, prediction: AgentPredictionEntity) -> bool:
        """Determines if a prediction needs human-in-the-loop validation."""
        confidence = prediction.confidence_score
        # Determine if we need review based on confidence and type
        prediction_type = prediction.prediction_type

        if confidence is None or prediction_type is None:
            return True

        # Rule 1: CRITICAL risk always needs review
        if prediction_type == BurnoutRiskLevel.CRITICAL:
            return True

        # Rule 2: HIGH risk with low confidence (< 0.75)
        if prediction_type == BurnoutRiskLevel.HIGH:
            return confidence < 0.75

        # Rule 3: MEDIUM risk with low confidence (< 0.70)
        if prediction_type == BurnoutRiskLevel.MEDIUM:
            return confidence < 0.70

        # Rule 4: General confidence threshold
        return confidence < self.confidence_threshold

    def should_send_critical_alert(self, current_streak: int) -> bool:
        """Implements the escalating notification policy."""
        if current_streak == self.CRITICAL_STREAK_THRESHOLD:
            return True
        if current_streak == 7 or current_streak == 14:
            return True
        if current_streak > 14 and (current_streak - 14) % 7 == 0:
            return True
        return False

    def get_recent_history(self, employee_id: int, days: int) -> List[Dict]:
        """Fetches and formats historical predictions from the database."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        daily_logs = self.daily_log_repository.get_by_date_range(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date
        )

        if not daily_logs:
            return []

        history = []
        for daily_log in daily_logs:
            predictions = self.prediction_repository.get_by_daily_log(daily_log.id)
            if predictions:
                prediction = predictions[0]

                try:
                    burnout_rate = float(prediction.prediction_value) if prediction.prediction_value else 0.0
                except (ValueError, TypeError):
                    burnout_rate = 0.0

                prediction_type = prediction.prediction_type or BurnoutRiskLevel.from_burnout_rate(burnout_rate)

                if hasattr(prediction_type, 'value'):
                    prediction_type = prediction_type.value

                history.append({
                    'date': daily_log.log_date,
                    'rate': burnout_rate,
                    'level': prediction_type
                })

        history.sort(key=lambda x: x['date'], reverse=True)
        return history[:days]