from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentPredictionCreateRequest(BaseModel):
    """DTO for creating a new agent prediction."""
    daily_log_id: int = Field(..., description="Daily log ID")
    burnout_risk: str = Field(..., min_length=1, max_length=50, description="Risk level (e.g. 'High', 'Low')")
    burnout_rate: Optional[float] = Field(None, description="Burnout rate value")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "daily_log_id": 1,
                "burnout_risk": "HIGH",
                "burnout_rate": 0.85,
                "confidence_score": 0.87
            }
        }


class AgentPredictionUpdateRequest(BaseModel):
    """DTO for updating an existing agent prediction."""
    daily_log_id: Optional[int] = Field(None, description="Daily log ID")
    burnout_risk: Optional[str] = Field(None, min_length=1, max_length=50, description="Risk level")
    burnout_rate: Optional[float] = Field(None, description="Burnout rate value")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "burnout_risk": "MEDIUM",
                "confidence_score": 0.92
            }
        }


class AgentPredictionResponse(BaseModel):
    """DTO for agent prediction responses."""
    id: int = Field(..., description="Prediction ID")
    daily_log_id: int = Field(..., description="Daily log ID")
    burnout_risk: str = Field(..., description="Risk level")
    burnout_rate: Optional[float] = Field(None, description="Burnout rate value")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    confidence_percentage: str = Field(..., description="Confidence as percentage")
    created_at: datetime = Field(..., description="Date prediction was created")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "daily_log_id": 1,
                "burnout_risk": "HIGH",
                "burnout_rate": 0.85,
                "confidence_score": 0.87,
                "confidence_percentage": "87.0%",
                "created_at": "2024-01-15T10:30:00"
            }
        }
