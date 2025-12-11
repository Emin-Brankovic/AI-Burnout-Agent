import string
from pydantic import BaseModel

class BurnoutFeatures(BaseModel):
    social_interactions: float
    fatigue_level: float
    physical_activity_minutes: float
    stress_level: float
    sleep_hours: float
    workload: float
    anxiety_level: float
    mood_score: float
    timestamp:string