from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentPredictionCreateRequest(BaseModel):
    """DTO for creating a new agent prediction."""
    daily_log_id: int = Field(..., description="Daily log ID")
    prediction_type: str = Field(..., min_length=1, max_length=50, description="Type of prediction")
    prediction_value: Optional[str] = Field(None, description="Prediction value/result")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "daily_log_id": 1,
                "prediction_type": "burnout_risk",
                "prediction_value": "HIGH",
                "confidence_score": 0.87
            }
        }


class AgentPredictionUpdateRequest(BaseModel):
    """DTO for updating an existing agent prediction."""
    daily_log_id: Optional[int] = Field(None, description="Daily log ID")
    prediction_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Type of prediction")
    prediction_value: Optional[str] = Field(None, description="Prediction value/result")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_value": "MEDIUM",
                "confidence_score": 0.92
            }
        }


class AgentPredictionResponse(BaseModel):
    """DTO for agent prediction responses."""
    id: int = Field(..., description="Prediction ID")
    daily_log_id: int = Field(..., description="Daily log ID")
    prediction_type: str = Field(..., description="Type of prediction")
    prediction_value: Optional[str] = Field(None, description="Prediction value/result")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    confidence_percentage: str = Field(..., description="Confidence as percentage")
    created_at: datetime = Field(..., description="Date prediction was created")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "daily_log_id": 1,
                "prediction_type": "burnout_risk",
                "prediction_value": "HIGH",
                "confidence_score": 0.87,
                "confidence_percentage": "87.0%",
                "created_at": "2024-01-15T10:30:00"
            }
        }
