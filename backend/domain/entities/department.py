"""Department domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DepartmentEntity:
    """Department domain entity - pure Python, no database dependencies."""

    name: str
    description: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Department name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Department name cannot exceed 100 characters")

    def __str__(self) -> str:
        return f"Department: {self.name}"
