from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class DailyLogCreateRequest(BaseModel):
    """DTO for creating a new daily log."""
    employee_id: int = Field(..., description="Employee ID")
    log_date: Optional[datetime] = Field(None, description="Log date (defaults to now if not provided)")
    hours_worked: Optional[float] = Field(None, ge=0, le=24, description="Hours worked (0-24)")
    hours_slept: Optional[float] = Field(None, ge=0, le=24, description="Hours slept (0-24)")
    daily_personal_time: Optional[float] = Field(None, ge=0, description="Personal time in hours")
    motivation_level: Optional[int] = Field(None, ge=1, le=10, description="Motivation level (1-10)")
    stress_level: Optional[int] = Field(None, ge=1, le=10, description="Stress level (1-10)")
    workload_intensity: Optional[int] = Field(None, ge=1, le=10, description="Workload intensity (1-10)")
    overtime_hours_today: Optional[float] = Field(None, ge=0, description="Overtime hours")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 1,
                "log_date": "2024-01-15T00:00:00",
                "hours_worked": 8.5,
                "hours_slept": 7.0,
                "daily_personal_time": 2.0,
                "motivation_level": 7,
                "stress_level": 5,
                "workload_intensity": 6,
                "overtime_hours_today": 0.5
            }
        }


class DailyLogUpdateRequest(BaseModel):
    """DTO for updating an existing daily log."""
    log_date: Optional[datetime] = Field(None, description="Log date")
    hours_worked: Optional[float] = Field(None, ge=0, le=24, description="Hours worked (0-24)")
    hours_slept: Optional[float] = Field(None, ge=0, le=24, description="Hours slept (0-24)")
    daily_personal_time: Optional[float] = Field(None, ge=0, description="Personal time in hours")
    motivation_level: Optional[int] = Field(None, ge=1, le=10, description="Motivation level (1-10)")
    stress_level: Optional[int] = Field(None, ge=1, le=10, description="Stress level (1-10)")
    workload_intensity: Optional[int] = Field(None, ge=1, le=10, description="Workload intensity (1-10)")
    overtime_hours_today: Optional[float] = Field(None, ge=0, description="Overtime hours")

    class Config:
        json_schema_extra = {
            "example": {
                "hours_worked": 9.0,
                "stress_level": 6,
                "overtime_hours_today": 1.0
            }
        }


class DailyLogResponse(BaseModel):
    """DTO for daily log responses."""
    id: int = Field(..., description="Daily log ID")
    employee_id: int = Field(..., description="Employee ID")
    log_date: datetime = Field(..., description="Log date")
    hours_worked: Optional[float] = Field(None, description="Hours worked")
    hours_slept: Optional[float] = Field(None, description="Hours slept")
    daily_personal_time: Optional[float] = Field(None, description="Personal time")
    motivation_level: Optional[int] = Field(None, description="Motivation level (1-10)")
    stress_level: Optional[int] = Field(None, description="Stress level (1-10)")
    workload_intensity: Optional[int] = Field(None, description="Workload intensity (1-10)")
    overtime_hours_today: Optional[float] = Field(None, description="Overtime hours")
    burnout_risk: str = Field(..., description="Calculated burnout risk (LOW/MEDIUM/HIGH)")
    burnout_rate: Optional[float] = Field(None, description="Predicted or calculated burnout rate")
    status: Optional[str] = Field(None, description="Log processing status")
    processed_at: Optional[datetime] = Field(None, description="When the log was last processed")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "employee_id": 1,
                "log_date": "2024-01-15T00:00:00",
                "hours_worked": 8.5,
                "hours_slept": 7.0,
                "daily_personal_time": 2.0,
                "motivation_level": 7,
                "stress_level": 5,
                "workload_intensity": 6,
                "overtime_hours_today": 0.5,
                "burnout_risk": "LOW",
                "burnout_rate": 0.13
            }
        }
class DailyLogWithPredictionResponse(DailyLogResponse):
    """DTO for daily log with associated prediction."""
    burnout_risk: Optional[str] = Field(None, description="Prediction Type")
    burnout_rate: Optional[float] = Field(None, description="Prediction Value")
    confidence_score: Optional[float] = Field(None, description="Confidence Score")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "employee_id": 1,
                # ... inherit other fields ...
                "burnout_risk": "HIGH",
                "burnout_rate": 0.85,
                "confidence_score": 0.92
            }
        }

#Ovo je ono sto uzme iz baze pa treba obrisati
class BatchEnqueueRequest(BaseModel):
    """DTO for batch enqueueing daily logs for prediction."""
    batch_size: int = Field(..., ge=1, le=1000, description="Number of daily logs to enqueue (1-1000)")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_size": 50
            }
        }

#Ovo je ono sto uzme iz baze pa treba obrisati
class BatchEnqueueResponse(BaseModel):
    """DTO for batch enqueue operation response."""
    enqueued_count: int = Field(..., description="Number of logs successfully enqueued")
    requested_count: int = Field(..., description="Number of logs requested")
    enqueued_logs: List[DailyLogResponse] = Field(..., description="Details of enqueued logs")

    class Config:
        json_schema_extra = {
            "example": {
                "enqueued_count": 50,
                "requested_count": 50,
                "enqueued_logs": []
            }
        }

#Ovo dvoje je okay
class GenerateLogsRequest(BaseModel):
    """DTO for generating random daily logs."""
    batch_size: int = Field(..., ge=1, le=1000, description="Number of random daily logs to generate (1-1000)")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_size": 20
            }
        }


class GenerateLogsResponse(BaseModel):
    """DTO for generate logs operation response."""
    generated_count: int = Field(..., description="Number of logs successfully generated")
    requested_count: int = Field(..., description="Number of logs requested")
    generated_logs: List[DailyLogResponse] = Field(..., description="Details of generated logs")

    class Config:
        json_schema_extra = {
            "example": {
                "generated_count": 20,
                "requested_count": 20,
                "generated_logs": []
            }
        }

