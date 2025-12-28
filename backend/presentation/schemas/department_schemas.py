from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DepartmentCreateRequest(BaseModel):
    """DTO for creating a new department."""
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    description: Optional[str] = Field(None, description="Department description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Engineering",
                "description": "Software development and engineering team"
            }
        }


class DepartmentUpdateRequest(BaseModel):
    """DTO for updating an existing department."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Department name")
    description: Optional[str] = Field(None, description="Department description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Engineering & Technology",
                "description": "Updated description"
            }
        }


class DepartmentResponse(BaseModel):
    """DTO for department responses."""
    id: int = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    description: Optional[str] = Field(None, description="Department description")
    created_at: datetime = Field(..., description="Date department was created")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Engineering",
                "description": "Software development team",
                "created_at": "2024-01-01T00:00:00"
            }
        }
