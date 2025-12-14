from pydantic import BaseModel,Field

class BurnoutFeatures(BaseModel):
    social_interactions: float = Field(..., ge=0, le=50, description="Number of daily social interactions")
    fatigue_level: float = Field(..., ge=0, le=10, description="Fatigue from 0–10")
    physical_activity_minutes: float = Field(..., ge=0, le=300, description="Minutes of physical activity")
    stress_level: float = Field(..., ge=0, le=10, description="Stress from 0–10")
    sleep_hours: float = Field(..., ge=0, le=24, description="Hours slept")
    workload: float = Field(..., ge=0, le=100, description="Workload score 0–100")
    anxiety_level: float = Field(..., ge=0, le=10, description="Anxiety from 0–10")
    mood_score: float = Field(..., ge=0, le=10, description="Mood from 0–10")
    timestamp: str = Field(..., description="Timestamp in ISO format")

class BurnoutPredictionResponse(BaseModel):
    Prediction: str
    Reliability: dict[str, str]
