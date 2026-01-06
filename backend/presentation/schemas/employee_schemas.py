from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EmployeeCreateRequest(BaseModel):
    """DTO for creating a new employee."""
    first_name: str = Field(..., min_length=1, max_length=50, description="Employee's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Employee's last name")
    email: str = Field(..., description="Employee's email address")
    department_id: Optional[int] = Field(None, description="Department ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "department_id": 1
            }
        }


class EmployeeUpdateRequest(BaseModel):
    """DTO for updating an existing employee."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Employee's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Employee's last name")
    email: Optional[str] = Field(None, description="Employee's email address")
    department_id: Optional[int] = Field(None, description="Department ID")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "email": "jane.doe@example.com",
                "department_id": 2
            }
        }


class EmployeeResponse(BaseModel):
    """DTO for employee responses."""
    id: int = Field(..., description="Employee ID")
    first_name: str = Field(..., description="Employee's first name")
    last_name: str = Field(..., description="Employee's last name")
    email: str = Field(..., description="Employee's email address")
    department_id: Optional[int] = Field(None, description="Department ID")
    hire_date: datetime = Field(..., description="Date employee was hired")
    full_name: str = Field(..., description="Employee's full name")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "department_id": 1,
                "hire_date": "2024-01-15T10:30:00",
                "full_name": "John Doe"
            }
        }


class EmployeePaginatedResponse(BaseModel):
    """DTO for paginated employee responses."""
    employees: List[EmployeeResponse] = Field(..., description="List of employees")
    total: int = Field(..., description="Total number of employees")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "employees": [
                    {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "department_id": 1,
                        "hire_date": "2024-01-15T10:30:00",
                        "full_name": "John Doe"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "total_pages": 5
            }
        }
