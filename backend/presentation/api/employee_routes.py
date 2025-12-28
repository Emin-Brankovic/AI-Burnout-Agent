from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.infrastructure.persistence.database import get_db
from backend.application.services.employee_service import EmployeeService
from backend.presentation.schemas.employee_schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse
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


@router.get("/", response_model=List[EmployeeResponse])
def get_all_employees(
        page: Optional[int] = Query(None, ge=1),
        page_size: Optional[int] = Query(None, ge=1, le=100),
        department_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """Get all employees with optional filtering and pagination."""
    try:
        service = EmployeeService(db)

        if department_id:
            entities = service.get_by_department(department_id)
        else:
            result = service.get_all()
            entities = result.items

        return [
            EmployeeResponse(
                id=entity.id,
                first_name=entity.first_name,
                last_name=entity.last_name,
                email=entity.email,
                department_id=entity.department_id,
                hire_date=entity.hire_date,
                full_name=entity.get_full_name()
            )
            for entity in entities
        ]
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
