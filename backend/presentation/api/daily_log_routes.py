from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import traceback

from backend.infrastructure.persistence.database import get_db
from backend.application.services.daily_log_service import DailyLogService
from backend.presentation.schemas.daily_log_schemas import (
    DailyLogCreateRequest,
    DailyLogUpdateRequest,
    DailyLogResponse
)

router = APIRouter(prefix="/daily-logs", tags=["Daily Logs"])


@router.post("/", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
def create_daily_log(
        request: DailyLogCreateRequest,
        db: Session = Depends(get_db)
):
    """Create a new daily log."""
    try:
        service = DailyLogService(db)
        entity = service.create(request)

        return DailyLogResponse(
            id=entity.id,
            employee_id=entity.employee_id,
            log_date=entity.log_date,
            hours_worked=entity.hours_worked,
            hours_slept=entity.hours_slept,
            daily_personal_time=entity.daily_personal_time,
            motivation_level=entity.motivation_level,
            stress_level=entity.stress_level,
            workload_intensity=entity.workload_intensity,
            overtime_hours_today=entity.overtime_hours_today,
            burnout_risk=entity.calculate_burnout_risk(),
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:

        db.rollback()
        tb = traceback.format_exc()  # 👈 captures full stack trace as string
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=tb
        )


@router.get("/", response_model=List[DailyLogResponse])
def get_all_daily_logs(
        page: Optional[int] = Query(None, ge=1),
        page_size: Optional[int] = Query(None, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """Get all daily logs with optional pagination."""
    try:
        service = DailyLogService(db)
        result = service.get_all()

        return [
            DailyLogResponse(
                id=entity.id,
                employee_id=entity.employee_id,
                log_date=entity.log_date,
                hours_worked=entity.hours_worked,
                hours_slept=entity.hours_slept,
                daily_personal_time=entity.daily_personal_time,
                motivation_level=entity.motivation_level,
                stress_level=entity.stress_level,
                workload_intensity=entity.workload_intensity,
                overtime_hours_today=entity.overtime_hours_today,
                burnout_risk=entity.calculate_burnout_risk(),
                burnout_rate=entity.calculate_burnout_rate()
            )
            for entity in result.items
        ]
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.get("/{log_id}", response_model=DailyLogResponse)
def get_daily_log(log_id: int, db: Session = Depends(get_db)):
    """Get daily log by ID."""
    try:
        service = DailyLogService(db)
        entity = service.get_by_id(log_id)

        return DailyLogResponse(
            id=entity.id,
            employee_id=entity.employee_id,
            log_date=entity.log_date,
            hours_worked=entity.hours_worked,
            hours_slept=entity.hours_slept,
            daily_personal_time=entity.daily_personal_time,
            motivation_level=entity.motivation_level,
            stress_level=entity.stress_level,
            workload_intensity=entity.workload_intensity,
            overtime_hours_today=entity.overtime_hours_today,
            burnout_risk=entity.calculate_burnout_risk(),
            burnout_rate=entity.calculate_burnout_rate()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/employee/{employee_id}", response_model=List[DailyLogResponse])
def get_logs_by_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get all logs for a specific employee."""
    try:
        service = DailyLogService(db)
        entities = service.get_by_employee(employee_id)

        return [
            DailyLogResponse(
                id=entity.id,
                employee_id=entity.employee_id,
                log_date=entity.log_date,
                hours_worked=entity.hours_worked,
                hours_slept=entity.hours_slept,
                daily_personal_time=entity.daily_personal_time,
                motivation_level=entity.motivation_level,
                stress_level=entity.stress_level,
                workload_intensity=entity.workload_intensity,
                overtime_hours_today=entity.overtime_hours_today,
                burnout_risk=entity.calculate_burnout_risk(),
                burnout_rate=entity.calculate_burnout_rate()
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/employee/{employee_id}/date-range", response_model=List[DailyLogResponse])
def get_logs_by_date_range(
        employee_id: int,
        start_date: datetime = Query(..., description="Start date (ISO format)"),
        end_date: datetime = Query(..., description="End date (ISO format)"),
        db: Session = Depends(get_db)
):
    """Get logs for employee within a date range."""
    try:
        service = DailyLogService(db)
        entities = service.get_by_date_range(employee_id, start_date, end_date)

        return [
            DailyLogResponse(
                id=entity.id,
                employee_id=entity.employee_id,
                log_date=entity.log_date,
                hours_worked=entity.hours_worked,
                hours_slept=entity.hours_slept,
                daily_personal_time=entity.daily_personal_time,
                motivation_level=entity.motivation_level,
                stress_level=entity.stress_level,
                workload_intensity=entity.workload_intensity,
                overtime_hours_today=entity.overtime_hours_today,
                burnout_risk=entity.calculate_burnout_risk(),
                burnout_rate=entity.calculate_burnout_rate()
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{log_id}", response_model=DailyLogResponse)
def update_daily_log(
        log_id: int,
        request: DailyLogUpdateRequest,
        db: Session = Depends(get_db)
):
    """Update an existing daily log."""
    try:
        service = DailyLogService(db)
        entity = service.update(log_id, request)

        return DailyLogResponse(
            id=entity.id,
            employee_id=entity.employee_id,
            log_date=entity.log_date,
            hours_worked=entity.hours_worked,
            hours_slept=entity.hours_slept,
            daily_personal_time=entity.daily_personal_time,
            motivation_level=entity.motivation_level,
            stress_level=entity.stress_level,
            workload_intensity=entity.workload_intensity,
            overtime_hours_today=entity.overtime_hours_today,
            burnout_risk=entity.calculate_burnout_risk(),
            burnout_rate=entity.calculate_burnout_rate()
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_log(log_id: int, db: Session = Depends(get_db)):
    """Delete a daily log by ID."""
    try:
        service = DailyLogService(db)
        service.delete(log_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
