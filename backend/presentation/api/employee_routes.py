from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.infrastructure.persistence.database import get_db
from backend.application.services.employee_service import EmployeeService
from backend.presentation.schemas.employee_schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse,
    EmployeePaginatedResponse
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
        request: EmployeeCreateRequest,
        db: Session = Depends(get_db)
):
    """Create a new employee."""
    try:
        service = EmployeeService(db)
        entity = service.create(request)

        return EmployeeResponse(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            department_id=entity.department_id,
            hire_date=entity.hire_date,
            full_name=entity.get_full_name()
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=EmployeePaginatedResponse)
def get_all_employees(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Items per page"),
        department_id: Optional[int] = Query(None, description="Filter by department ID"),
        db: Session = Depends(get_db)
):
    """Get all employees with pagination and optional filtering.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - department_id: Filter by department ID (optional)
    """
    try:
        service = EmployeeService(db)

        # Get all employees (filtered by department if specified)
        if department_id:
            all_entities = service.get_by_department(department_id)
        else:
            result = service.get_all()
            all_entities = result.items
        
        # Calculate pagination
        total_count = len(all_entities)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entities = all_entities[start_idx:end_idx]
        
        # Calculate total pages
        import math
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0

        # Build response
        employees = [
            EmployeeResponse(
                id=entity.id,
                first_name=entity.first_name,
                last_name=entity.last_name,
                email=entity.email,
                department_id=entity.department_id,
                hire_date=entity.hire_date,
                full_name=entity.get_full_name()
            )
            for entity in paginated_entities
        ]
        
        return EmployeePaginatedResponse(
            employees=employees,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID."""
    try:
        service = EmployeeService(db)
        entity = service.get_by_id(employee_id)

        return EmployeeResponse(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            department_id=entity.department_id,
            hire_date=entity.hire_date,
            full_name=entity.get_full_name()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
        employee_id: int,
        request: EmployeeUpdateRequest,
        db: Session = Depends(get_db)
):
    """Update an existing employee."""
    try:
        service = EmployeeService(db)
        entity = service.update(employee_id, request)

        return EmployeeResponse(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            department_id=entity.department_id,
            hire_date=entity.hire_date,
            full_name=entity.get_full_name()
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete an employee by ID."""
    try:
        service = EmployeeService(db)
        service.delete(employee_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/email/{email}", response_model=EmployeeResponse)
def get_employee_by_email(email: str, db: Session = Depends(get_db)):
    """Get employee by email address."""
    try:
        service = EmployeeService(db)
        entity = service.get_by_email(email)

        return EmployeeResponse(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            department_id=entity.department_id,
            hire_date=entity.hire_date,
            full_name=entity.get_full_name()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
