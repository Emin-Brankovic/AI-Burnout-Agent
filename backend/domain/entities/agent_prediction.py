"""AgentPrediction domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AgentPredictionEntity:
    """AgentPrediction domain entity - pure Python, no database dependencies."""

    daily_log_id: int
    prediction_type: str
    prediction_value: Optional[str] = None
    confidence_score: Optional[float] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.prediction_type or not self.prediction_type.strip():
            raise ValueError("Prediction type cannot be empty")
        if len(self.prediction_type) > 50:
            raise ValueError("Prediction type cannot exceed 50 characters")
        if self.confidence_score is not None and (self.confidence_score < 0 or self.confidence_score > 1):
            raise ValueError("Confidence score must be between 0 and 1")

    def is_high_confidence(self) -> bool:
        """Check if prediction has high confidence."""
        if self.confidence_score is None:
            return False
        return self.confidence_score >= 0.8

    def get_confidence_percentage(self) -> str:
        """Get confidence score as percentage string."""
        if self.confidence_score is None:
            return "N/A"
        return f"{self.confidence_score * 100:.1f}%"

    def __str__(self) -> str:
        return f"Prediction: {self.prediction_type} ({self.get_confidence_percentage()})"
