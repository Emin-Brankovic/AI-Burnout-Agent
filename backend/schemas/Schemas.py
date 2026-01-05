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

class EmployeeData(BaseModel):
    Employee_Id: int
    Work_Hours_Per_Day: float
    Sleep_Hours_Per_Night: float
    Personal_Time_Hours_Per_Day: float
    Motivation_Level: int
    Work_Stress_Level: int
    Workload_Intensity: int
    Overtime_Hours_Today: float


class PredictionResult(BaseModel):
    probability: float
    prediction_type: str
    message: str
    #recommendation: str

class BurnoutPredictionResponse(BaseModel):
    Prediction: str
    Reliability: dict[str, str]
