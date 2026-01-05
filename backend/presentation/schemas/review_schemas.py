from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.presentation.schemas.agent_prediction_schemas import AgentPredictionResponse
from backend.presentation.schemas.daily_log_schemas import DailyLogResponse

class ReviewSubmitRequest(BaseModel):
    """DTO for submitting HR review of a prediction."""
    is_correct: bool = Field(..., description="Whether the prediction was correct")
    hr_notes: Optional[str] = Field(None, description="Optional notes from HR")

    class Config:
        json_schema_extra = {
            "example": {
                "is_correct": True,
                "hr_notes": "Confirmed with employee, they are feeling burnt out."
            }
        }

class ReviewDetailsResponse(BaseModel):
    """DTO for review details context."""
    prediction: AgentPredictionResponse
    log_data: DailyLogResponse
    confidence_score: float
    ai_prediction_type: str

    class Config:
        from_attributes = True
