from datetime import datetime
import traceback

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.application.services.prediction_service import get_prediction_service
from backend.domain.entities.daily_log import DailyLogEntity
from backend.infrastructure.persistence.database import get_db
from backend.application.services.agent_prediction_service import AgentPredictionService
from backend.application.services.base_service import BaseSearchObject
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from backend.presentation.schemas import DailyLogCreateRequest
from backend.presentation.schemas.agent_prediction_schemas import (
    AgentPredictionCreateRequest,
    AgentPredictionUpdateRequest,
    AgentPredictionResponse
)

router = APIRouter(prefix="/predictions", tags=["Agent Predictions"])


@router.post("/predict", response_model=dict, status_code=status.HTTP_200_OK)
def predict_burnout(
    request: DailyLogCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Predict burnout risk based on user input without saving daily log.

    This endpoint allows direct prediction from user input data.
    """
    try:
        # Create a temporary DailyLogEntity for prediction (not saved to DB)
        temp_daily_log = DailyLogEntity(
            id=None,  # Temporary, not persisted
            employee_id=request.employee_id,
            log_date=request.log_date or datetime.now(),
            hours_worked=request.hours_worked,
            hours_slept=request.hours_slept,
            daily_personal_time=request.daily_personal_time,
            motivation_level=request.motivation_level,
            stress_level=request.stress_level,
            workload_intensity=request.workload_intensity,
            overtime_hours_today=request.overtime_hours_today
        )


        # Initialize prediction service
        prediction_repo = AgentPredictionRepository(db)
        daily_log_repository = DailyLogRepository(db)
        employee_repository = EmployeeRepository(db)
        prediction_service = get_prediction_service(
            prediction_repository=prediction_repo,
            daily_log_repository=daily_log_repository,
            employee_repository=employee_repository
        )

        # Make prediction (save_to_db=False to avoid storing prediction)
        prediction_entity = prediction_service.predict_for_daily_log(
            daily_log=temp_daily_log,
            save_to_db=True
        )

        db.commit()

        # Return prediction results
        return {
            "employee_id": request.employee_id,
            "input_data": {
                "hours_worked": request.hours_worked,
                "hours_slept": request.hours_slept,
                "daily_personal_time": request.daily_personal_time,
                "motivation_level": request.motivation_level,
                "stress_level": request.stress_level,
                "workload_intensity": request.workload_intensity,
                "overtime_hours_today": request.overtime_hours_today
            },
            "prediction": {
                "burnout_rate": prediction_entity.prediction_value,
                "prediction_type": prediction_entity.prediction_type,
                "confidence_score": prediction_entity.confidence_score,
                "confidence_percentage": prediction_entity.get_confidence_percentage(),
                "message": getattr(prediction_entity, 'message', None)
            },
            "timestamp": datetime.now().isoformat()
        }

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Prediction failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
@router.post("/", response_model=AgentPredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
        request: AgentPredictionCreateRequest,
        db: Session = Depends(get_db)
):
    """Create a new prediction."""
    try:
        service = AgentPredictionService(db)
        entity = service.create(request)

        return AgentPredictionResponse(
            id=entity.id,
            daily_log_id=entity.daily_log_id,
            prediction_type=entity.prediction_type,
            prediction_value=entity.prediction_value,
            confidence_score=entity.confidence_score,
            confidence_percentage=entity.get_confidence_percentage(),
            created_at=entity.created_at
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=traceback.format_exc())


@router.get("/", response_model=List[AgentPredictionResponse])
def get_all_predictions(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """Get all predictions with optional pagination."""
    try:
        service = AgentPredictionService(db)
        search = BaseSearchObject(page=page, page_size=page_size)
        result = service.get_all(search)

        return [
            AgentPredictionResponse(
                id=entity.id,
                daily_log_id=entity.daily_log_id,
                prediction_type=entity.prediction_type,
                prediction_value=entity.prediction_value,
                confidence_score=entity.confidence_score,
                confidence_percentage=entity.get_confidence_percentage(),
                created_at=entity.created_at
            )
            for entity in result.items
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{prediction_id}", response_model=AgentPredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get prediction by ID."""
    try:
        service = AgentPredictionService(db)
        entity = service.get_by_id(prediction_id)

        return AgentPredictionResponse(
            id=entity.id,
            daily_log_id=entity.daily_log_id,
            prediction_type=entity.prediction_type,
            prediction_value=entity.prediction_value,
            confidence_score=entity.confidence_score,
            confidence_percentage=entity.get_confidence_percentage(),
            created_at=entity.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/daily-log/{daily_log_id}", response_model=List[AgentPredictionResponse])
def get_predictions_by_daily_log(daily_log_id: int, db: Session = Depends(get_db)):
    """Get all predictions for a specific daily log."""
    try:
        service = AgentPredictionService(db)
        entities = service.get_by_daily_log(daily_log_id)

        return [
            AgentPredictionResponse(
                id=entity.id,
                daily_log_id=entity.daily_log_id,
                prediction_type=entity.prediction_type,
                prediction_value=entity.prediction_value,
                confidence_score=entity.confidence_score,
                confidence_percentage=entity.get_confidence_percentage(),
                created_at=entity.created_at
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/daily-log/{daily_log_id}/high-confidence", response_model=List[AgentPredictionResponse])
def get_high_confidence_predictions(daily_log_id: int, db: Session = Depends(get_db)):
    """Get only high confidence predictions for a daily log."""
    try:
        service = AgentPredictionService(db)
        entities = service.get_high_confidence_predictions(daily_log_id)

        return [
            AgentPredictionResponse(
                id=entity.id,
                daily_log_id=entity.daily_log_id,
                prediction_type=entity.prediction_type,
                prediction_value=entity.prediction_value,
                confidence_score=entity.confidence_score,
                confidence_percentage=entity.get_confidence_percentage(),
                created_at=entity.created_at
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/type/{prediction_type}", response_model=List[AgentPredictionResponse])
def get_predictions_by_type(prediction_type: str, db: Session = Depends(get_db)):
    """Get all predictions of a specific type."""
    try:
        service = AgentPredictionService(db)
        entities = service.get_by_type(prediction_type)

        return [
            AgentPredictionResponse(
                id=entity.id,
                daily_log_id=entity.daily_log_id,
                prediction_type=entity.prediction_type,
                prediction_value=entity.prediction_value,
                confidence_score=entity.confidence_score,
                confidence_percentage=entity.get_confidence_percentage(),
                created_at=entity.created_at
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{prediction_id}", response_model=AgentPredictionResponse)
def update_prediction(
        prediction_id: int,
        request: AgentPredictionUpdateRequest,
        db: Session = Depends(get_db)
):
    """Update an existing prediction."""
    try:
        service = AgentPredictionService(db)
        entity = service.update(prediction_id, request)

        return AgentPredictionResponse(
            id=entity.id,
            daily_log_id=entity.daily_log_id,
            prediction_type=entity.prediction_type,
            prediction_value=entity.prediction_value,
            confidence_score=entity.confidence_score,
            confidence_percentage=entity.get_confidence_percentage(),
            created_at=entity.created_at
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Delete a prediction by ID."""
    try:
        service = AgentPredictionService(db)
        service.delete(prediction_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
