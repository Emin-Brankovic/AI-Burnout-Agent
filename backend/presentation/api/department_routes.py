from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.infrastructure.persistence.database import get_db
from backend.application.services.department_service import DepartmentService
from backend.presentation.schemas.department_schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentResponse
)

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
        request: DepartmentCreateRequest,
        db: Session = Depends(get_db)
):
    """Create a new department."""

    service = DepartmentService(db)
    entity = service.create(request)

    return DepartmentResponse(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at
    )



@router.get("/", response_model=List[DepartmentResponse])
def get_all_departments(
        page: Optional[int] = Query(None, ge=1),
        page_size: Optional[int] = Query(None, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """Get all departments with optional pagination."""
    try:
        service = DepartmentService(db)
        result = service.get_all()

        return [
            DepartmentResponse(
                id=entity.id,
                name=entity.name,
                description=entity.description,
                created_at=entity.created_at
            )
            for entity in result.items
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    """Get department by ID."""
    try:
        service = DepartmentService(db)
        entity = service.get_by_id(department_id)

        return DepartmentResponse(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
        department_id: int,
        request: DepartmentUpdateRequest,
        db: Session = Depends(get_db)
):
    """Update an existing department."""
    try:
        service = DepartmentService(db)
        entity = service.update(department_id, request)

        return DepartmentResponse(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    """Delete a department by ID."""
    try:
        service = DepartmentService(db)
        service.delete(department_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/name/{name}", response_model=DepartmentResponse)
def get_department_by_name(name: str, db: Session = Depends(get_db)):
    """Get department by name."""
    try:
        service = DepartmentService(db)
        entity = service.get_by_name(name)

        return DepartmentResponse(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
