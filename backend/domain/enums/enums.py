"""
Domain Enums for Burnout Detection System

Defines legal statuses, risk levels, and domain types.
All enums follow FastAPI/Pydantic best practices.
"""

from enum import Enum
from typing import Tuple


class DailyLogStatus(str, Enum):
    """
    Status of a daily log entry through agent lifecycle.


    Flow:
    PENDING → PROCESSING → ANALYZED → REVIEWED
                        ↓
                      FAILED
    """
    QUEUED = "queued"  # Logged, awaiting agent analysis
    PROCESSING = "processing"  # Agent currently analyzing
    ANALYZED = "analyzed"  # Analysis complete (high confidence)
    PENDING_REVIEW = "pending_review"  # Needs manager review (borderline case)
    REVIEWED = "reviewed"  # Manager confirmed/corrected
    FAILED = "failed"  # Error during analysis

    @property
    def display_name(self) -> str:
        """User-friendly name"""
        names = {
            "pending": "Pending Analysis",
            "processing": "Processing...",
            "analyzed": "Analyzed",
            "pending_review": "Awaiting Review",
            "reviewed": "Reviewed",
            "failed": "Failed"
        }
        return names[self.value]



class BurnoutRiskLevel(str, Enum):
    """
    Burnout risk severity levels.

    Based on ML model prediction thresholds:
    - NORMAL:    0.00 - 0.30
    - LOW:       0.30 - 0.45
    - MEDIUM:    0.45 - 0.70
    - HIGH:      0.70 - 0.85
    - CRITICAL:  0.85 - 1.00
    """
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def display_name(self) -> str:
        """User-friendly name"""
        return self.value.title()

    @property
    def color(self) -> str:
        """UI color code"""
        colors = {
            "normal": "#22c55e",  # Green
            "low": "#84cc16",  # Light green
            "medium": "#eab308",  # Yellow
            "high": "#f97316",  # Orange
            "critical": "#ef4444"  # Red
        }
        return colors[self.value]


    @property
    def threshold_range(self) -> Tuple[float, float]:
        """Burnout rate threshold range (min, max)"""
        ranges = {
            "normal": (0.0, 0.30),
            "low": (0.30, 0.45),
            "medium": (0.45, 0.70),
            "high": (0.70, 0.85),
            "critical": (0.85, 1.00)
        }
        return ranges[self.value]

    @classmethod
    def from_burnout_rate(cls, rate: float) -> 'BurnoutRiskLevel':
        """
        Determine risk level from burnout rate prediction

        Args:
            rate: Burnout rate (0.0 to 1.0)

        Returns:
            Appropriate BurnoutRiskLevel
        """
        rate = max(0.0, min(1.0, rate))  # Clamp to [0, 1]

        if rate >= 0.85:
            return cls.CRITICAL
        elif rate >= 0.70:
            return cls.HIGH
        elif rate >= 0.45:
            return cls.MEDIUM
        elif rate >= 0.30:
            return cls.LOW
        else:
            return cls.NORMAL


class AgentActionType(str, Enum):
    """
    Types of actions the agent can take
    """
    NONE = "none"  # No action needed (healthy)
    MONITOR = "monitor"  # Continue monitoring
    RECOMMEND_BREAK = "recommend_break"  # Suggest time off
    ALERT = "alert"  # Send alert to manager
    ESCALATE = "escalate"  # Escalate to HR immediately

    @property
    def display_name(self) -> str:
        """User-friendly name"""
        names = {
            "none": "No Action Required",
            "monitor": "Continue Monitoring",
            "recommend_break": "Recommend Break",
            "alert": "Alert Manager",
            "escalate": "Escalate to HR"
        }
        return names[self.value]

    @property
    def requires_notification(self) -> bool:
        """Whether this action requires sending notification"""
        return self in [
            AgentActionType.ALERT,
            AgentActionType.ESCALATE
        ]

    @property
    def requires_immediate_action(self) -> bool:
        """Whether this requires immediate intervention"""
        return self == AgentActionType.ESCALATE


class PredictionConfidence(str, Enum):
    """
    Confidence level of ML prediction
    """
    VERY_LOW = "very_low"  # < 0.50
    LOW = "low"  # 0.50 - 0.70
    MEDIUM = "medium"  # 0.70 - 0.85
    HIGH = "high"  # 0.85 - 0.95
    VERY_HIGH = "very_high"  # > 0.95

    @classmethod
    def from_score(cls, score: float) -> 'PredictionConfidence':
        """
        Determine confidence from model confidence score

        Args:
            score: Confidence score (0.0 to 1.0)

        Returns:
            Appropriate PredictionConfidence
        """
        score = max(0.0, min(1.0, score))

        if score >= 0.95:
            return cls.VERY_HIGH
        elif score >= 0.85:
            return cls.HIGH
        elif score >= 0.70:
            return cls.MEDIUM
        elif score >= 0.50:
            return cls.LOW
        else:
            return cls.VERY_LOW


class TrainingMode(str, Enum):
    """
    Model training mode
    """
    INITIAL = "initial"  # First training from scratch
    INCREMENTAL = "incremental"  # Fine-tuning on new data
    FULL = "full"  # Complete retraining with all data

    @property
    def display_name(self) -> str:
        """User-friendly name"""
        names = {
            "initial": "Initial Training",
            "incremental": "Incremental Update",
            "full": "Full Retraining"
        }
        return names[self.value]


class NotificationChannel(str, Enum):
    """
    Channels for sending notifications
    """
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    IN_APP = "in_app"



# ============================================================================
# Testing & Validation
# ============================================================================

if __name__ == "__main__":
    print("✅ Domain Enums loaded\n")

    # Test BurnoutRiskLevel
    print("🔍 Testing BurnoutRiskLevel:")
    for rate in [0.1, 0.35, 0.55, 0.75, 0.90]:
        risk = BurnoutRiskLevel.from_burnout_rate(rate)
        print(f"   Rate {rate:.2f} →  {risk.display_name} (Color: {risk.color})")

    # Test AgentActionType
    print("\n🤖 Testing AgentActionType:")
    for action in AgentActionType:
        print(f"   {action.value}: {action.display_name}")
        print(f"      Notify: {action.requires_notification}, Urgent: {action.requires_immediate_action}")

    # Test PredictionConfidence
    print("\n📊 Testing PredictionConfidence:")
    for score in [0.45, 0.65, 0.78, 0.88, 0.97]:
        conf = PredictionConfidence.from_score(score)
        print(f"   Score {score:.2f} → {conf.value.title()}")

    # Test DailyLogStatus
    print("\n📝 Testing DailyLogStatus:")
    for status in DailyLogStatus:
        print(f"  {status.display_name}")

    print("\n✨ All enum tests passed!")
