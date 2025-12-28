"""DailyLog domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DailyLogEntity:
    """DailyLog domain entity - pure Python, no database dependencies."""

    employee_id: int
    log_date: datetime
    hours_worked: Optional[float] = None
    hours_slept: Optional[float] = None
    daily_personal_time: Optional[float] = None
    motivation_level: Optional[int] = None
    stress_level: Optional[int] = None
    workload_intensity: Optional[int] = None
    overtime_hours_today: Optional[float] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if self.hours_worked is not None and (self.hours_worked < 0 or self.hours_worked > 24):
            raise ValueError("Hours worked must be between 0 and 24")
        if self.hours_slept is not None and (self.hours_slept < 0 or self.hours_slept > 24):
            raise ValueError("Hours slept must be between 0 and 24")
        if self.daily_personal_time is not None and self.daily_personal_time < 0:
            raise ValueError("Personal time cannot be negative")
        if self.overtime_hours_today is not None and self.overtime_hours_today < 0:
            raise ValueError("Overtime hours cannot be negative")

        # Validate rating scales (1-10)
        self._validate_rating(self.motivation_level, "Motivation level")
        self._validate_rating(self.stress_level, "Stress level")
        self._validate_rating(self.workload_intensity, "Workload intensity")

    def _validate_rating(self, value: Optional[int], field_name: str):
        """Validate rating is between 1 and 10."""
        if value is not None and (value < 1 or value > 10):
            raise ValueError(f"{field_name} must be between 1 and 10")

    def is_overworked(self) -> bool:
        """Determine if employee is overworked based on metrics."""
        if self.hours_worked and self.hours_worked > 10:
            return True
        if self.stress_level and self.stress_level >= 8:
            return True
        if self.workload_intensity and self.workload_intensity >= 9:
            return True
        return False

    def calculate_burnout_risk(self) -> str:
        """Calculate burnout risk level."""
        risk_score = 0

        if self.hours_slept and self.hours_slept < 6:
            risk_score += 2
        if self.stress_level and self.stress_level >= 7:
            risk_score += 2
        if self.motivation_level and self.motivation_level <= 3:
            risk_score += 2
        if self.workload_intensity and self.workload_intensity >= 8:
            risk_score += 1
        if self.overtime_hours_today and self.overtime_hours_today > 2:
            risk_score += 1

        if risk_score >= 6:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def __str__(self) -> str:
        return f"DailyLog: Employee {self.employee_id} on {self.log_date.date()}"
