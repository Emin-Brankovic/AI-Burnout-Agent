from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import traceback

from backend.infrastructure.persistence.database import get_db
from backend.application.services.daily_log_service import DailyLogService
from backend.application.services.base_service import BaseSearchObject
from backend.presentation.schemas.daily_log_schemas import (
    DailyLogCreateRequest,
    DailyLogUpdateRequest,
    DailyLogResponse,
    DailyLogWithPredictionResponse
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
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """Get all daily logs with optional pagination."""
    try:
        service = DailyLogService(db)
        search = BaseSearchObject(page=page, page_size=page_size)
        result = service.get_all(search)

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


@router.get("/{log_id}/subsequent", response_model=List[DailyLogWithPredictionResponse])
def get_log_and_subsequent(log_id: int, db: Session = Depends(get_db)):
    """
    Get a specific daily log and the 7 logs immediately following it.
    Includes prediction details for each log.
    """
    try:
        service = DailyLogService(db)
        results = service.get_log_and_subsequent(log_id)

        response_list = []
        for item in results:
            pred_type = item.get("prediction_type")
            if hasattr(pred_type, "value"):
                pred_type = pred_type.value
            
            pass 

        
        return [
             DailyLogWithPredictionResponse(
                id=item["id"],
                employee_id=item["employee_id"],
                log_date=item["log_date"],
                hours_worked=item["hours_worked"],
                hours_slept=item["hours_slept"],
                daily_personal_time=item["daily_personal_time"],
                motivation_level=item["motivation_level"],
                stress_level=item["stress_level"],
                workload_intensity=item["workload_intensity"],
                overtime_hours_today=item["overtime_hours_today"],
                # Recalculate or rely on dict if service was fixed.
                # Since service sent dict without 'burnout_risk' key (it's a method on entity),
                # we must calc it or mapped it.
                burnout_risk=calculate_risk_helper(item), 
                burnout_rate=calculate_rate_helper(item),
                status=item.get("status"),
                processed_at=item.get("processed_at"),
                prediction_type=item["prediction_type"],
                prediction_value=item["prediction_value"],
                confidence_score=item["confidence_score"]
             )
             for item in results
        ]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def _calculate_risk_score_from_dict(item: dict) -> int:
    risk_score = 0
    hours_slept = item.get("hours_slept")
    stress_level = item.get("stress_level")
    motivation_level = item.get("motivation_level")
    workload = item.get("workload_intensity")
    overtime = item.get("overtime_hours_today")

    if hours_slept is not None and hours_slept < 6:
        risk_score += 2
    if stress_level is not None and stress_level >= 7:
        risk_score += 2
    if motivation_level is not None and motivation_level <= 3:
        risk_score += 2
    if workload is not None and workload >= 8:
        risk_score += 1
    if overtime is not None and overtime > 2:
        risk_score += 1
    return risk_score

def calculate_risk_helper(item: dict) -> str:
    score = _calculate_risk_score_from_dict(item)
    if score >= 6:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_rate_helper(item: dict) -> float:
    score = _calculate_risk_score_from_dict(item)
    val = round(score / 8.0, 2)
    return min(val, 1.0)  # Cap at 1.0 just in case logic evolves


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
