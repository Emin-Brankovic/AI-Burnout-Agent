from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.infrastructure.persistence.database import get_db
from backend.application.services.agent_prediction_service import AgentPredictionService
from backend.presentation.schemas.agent_prediction_schemas import (
    AgentPredictionCreateRequest,
    AgentPredictionUpdateRequest,
    AgentPredictionResponse
)

router = APIRouter(prefix="/predictions", tags=["Agent Predictions"])


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=List[AgentPredictionResponse])
def get_all_predictions(
        page: Optional[int] = Query(None, ge=1),
        page_size: Optional[int] = Query(None, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """Get all predictions with optional pagination."""
    try:
        service = AgentPredictionService(db)
        result = service.get_all()

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
