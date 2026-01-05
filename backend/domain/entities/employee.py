"""Employee domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class EmployeeEntity:
    """Employee domain entity - pure Python, no database dependencies."""

    first_name: str
    last_name: str
    email: str
    department_id: Optional[int] = None
    hire_date: Optional[datetime] = None
    id: Optional[int] = None
    high_burnout_streak: int = 0
    last_alert_sent: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        if len(self.first_name) > 50:
            raise ValueError("First name cannot exceed 50 characters")
        if len(self.last_name) > 50:
            raise ValueError("Last name cannot exceed 50 characters")
        if not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")

    def get_full_name(self) -> str:
        """Get employee's full name."""
        return f"{self.first_name} {self.last_name}"

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        return f"Employee: {self.get_full_name()} ({self.email})"
