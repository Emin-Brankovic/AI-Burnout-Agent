from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.presentation.schemas.agent_prediction_schemas import AgentPredictionResponse
from backend.presentation.schemas.daily_log_schemas import DailyLogResponse

class ReviewSubmitRequest(BaseModel):
    """DTO for submitting HR review of a prediction."""
    is_correct: bool = Field(..., description="Whether the prediction was correct")
    hr_notes: Optional[str] = Field(None, description="Optional notes from HR")
    hr_burnout_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="HR-corrected burnout rate (0.0-1.0). Used as gold label for retraining."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_correct": False,
                "hr_notes": "Employee is not burnt out, lowering rate.",
                "hr_burnout_rate": 0.25
            }
        }

class HistoricalRecord(BaseModel):
    """DTO for a single day of history."""
    log_date: datetime
    hours_worked: float
    stress_level: int
    prediction_type: Optional[str] = None
    prediction_value: Optional[float] = None
    confidence_score: Optional[float] = None

class ReviewDetailsResponse(BaseModel):
    """DTO for review details context."""
    prediction: AgentPredictionResponse
    log_data: DailyLogResponse
    confidence_score: float
    ai_prediction_type: str
    history: List[HistoricalRecord] = []

    class Config:
        from_attributes = True
