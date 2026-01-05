# backend/application/services/email_notification_service.py

"""
Email Notification Service - Business logic za burnout notifikacije
"""

from datetime import datetime
from typing import List, Dict
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.application.services.email_service import EmailService


class EmailNotificationService:
    """
    Servis za slanje burnout email notifikacija.
    Samo 2 tipa emailova:
    1. Critical Alert (sa historijom prethodnih predikcija)
    2. Review Request
    """

    def __init__(
            self,
            email_service: EmailService,
            recipient_email: str  # Jedan email za sve notifikacije
    ):
        self.email_service = email_service
        self.recipient_email = recipient_email

    # ========================================
    # PUBLIC API - Samo 2 metode
    # ========================================

    async def send_critical_alert(
            self,
            employee_id: int,
            employee_name: str,
            current_prediction: AgentPredictionEntity,
            recent_predictions: List[Dict],  # ✅ Lista prethodnih predikcija
            streak: int,
            log_date: datetime
    ) -> bool:
        """
        Šalje CRITICAL alert sa historijom prethodnih predikcija.

        Args:
            employee_id: ID zaposlenog
            employee_name: Ime zaposlenog
            current_prediction: Trenutna predikcija
            recent_predictions: Lista prethodnih predikcija [(date, rate, level), ...]
            streak: Broj uzastopnih CRITICAL dana
            log_date: Datum loga
        """
        subject = f"🚨 Critical Burnout Alert - Employee {employee_id} ({streak} days)"

        # ✅ Format prethodnih predikcija
        history_lines = []
        for pred in recent_predictions:
            history_lines.append(
                f"  {pred['date'].strftime('%Y-%m-%d')}: {pred['rate']:.1%} ({pred['level']})"
            )
        history_text = "\n".join(history_lines) if history_lines else "  (No previous data)"

        body = f"""CRITICAL BURNOUT ALERT

Employee: {employee_name} (ID: {employee_id})
Current Risk Level: CRITICAL
Current Burnout Rate: {current_prediction.burnout_rate:.1%}
Confidence: {current_prediction.confidence_score:.1%}
Consecutive Critical Days: {streak}
Date: {log_date.strftime('%Y-%m-%d')}

This employee has been in CRITICAL state for {streak} consecutive days.
Immediate action is required.

Recent History:
{history_text}

---
Burnout Prevention System
"""

        # Pošalji email
        return await self.email_service.send_email(
            to=[self.recipient_email],
            subject=subject,
            body_html=body,
            priority="urgent"
        )

    async def send_review_request(
            self,
            employee_id: int,
            employee_name: str,
            prediction: AgentPredictionEntity,
            log_date: datetime
    ) -> bool:
        """
        Šalje zahtjev za manual review.

        Args:
            employee_id: ID zaposlenog
            employee_name: Ime zaposlenog
            prediction: Predikcija za review
            log_date: Datum loga
        """
        subject = f"⚠️ Review Needed - Employee {employee_id}"

        body = f"""MANUAL REVIEW REQUIRED

Employee: {employee_name} (ID: {employee_id})

Burnout Rate: {self._fmt_percent(prediction.burnout_rate)}
Confidence: {self._fmt_percent(prediction.confidence_score)}
Date: {log_date.strftime('%Y-%m-%d')}

Low confidence prediction - manual review needed.

---
Burnout Prevention System
"""

        # Pošalji email
        return await self.email_service.send_email(
            to=[self.recipient_email],
            subject=subject,
            body_html=body,
            priority="normal"
        )

    def _fmt_percent(self, value: float | None) -> str:
        return f"{value:.1%}" if value is not None else "N/A"
