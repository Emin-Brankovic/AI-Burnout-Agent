from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import traceback

from backend.infrastructure.persistence.database import get_db
from backend.application.services.review_service import get_review_service, get_email_service
from backend.presentation.schemas.review_schemas import ReviewSubmitRequest, ReviewDetailsResponse
from backend.presentation.schemas.agent_prediction_schemas import AgentPredictionResponse
from backend.presentation.schemas.daily_log_schemas import DailyLogResponse

router = APIRouter(prefix="/reviews", tags=["Manual HR Review"])

@router.get("/pending", response_model=List[AgentPredictionResponse])
def get_pending_reviews(db: Session = Depends(get_db)):
    """Fetch all predictions that require HR attention."""
    try:
        service = get_review_service(db)
        entities = service.get_pending_reviews()
        
        return [
            AgentPredictionResponse(
                id=entity.id,
                daily_log_id=entity.daily_log_id,
                burnout_risk=entity.burnout_risk,
                burnout_rate=entity.burnout_rate,
                confidence_score=entity.confidence_score,
                confidence_percentage=entity.get_confidence_percentage(),
                created_at=entity.created_at
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending reviews: {str(e)}"
        )

@router.get("/{prediction_id}", response_model=ReviewDetailsResponse)
def get_review_details(prediction_id: int, db: Session = Depends(get_db)):
    """Get full context for HR to make an informed decision."""
    try:
        service = get_review_service(db)
        details = service.get_review_details(prediction_id)
        
        prediction = details["prediction"]
        log_data = details["log_data"]
        
        return ReviewDetailsResponse(
            prediction=AgentPredictionResponse(
                id=prediction.id,
                daily_log_id=prediction.daily_log_id,
                burnout_risk=prediction.burnout_risk,
                burnout_rate=prediction.burnout_rate,
                confidence_score=prediction.confidence_score,
                confidence_percentage=prediction.get_confidence_percentage(),
                created_at=prediction.created_at
            ),
            log_data=DailyLogResponse(
                id=log_data.id,
                employee_id=log_data.employee_id,
                log_date=log_data.log_date,
                hours_worked=log_data.hours_worked,
                hours_slept=log_data.hours_slept,
                daily_personal_time=log_data.daily_personal_time,
                motivation_level=log_data.motivation_level,
                stress_level=log_data.stress_level,
                workload_intensity=log_data.workload_intensity,
                overtime_hours_today=log_data.overtime_hours_today,
                burnout_risk=log_data.calculate_burnout_risk(),
                burnout_rate=log_data.calculate_burnout_rate(),
                status=log_data.status.value if hasattr(log_data.status, "value") else log_data.status,
                processed_at=log_data.processed_at
            ),
            confidence_score=details["confidence_score"],
            ai_prediction_type=details["ai_prediction_type"].value if hasattr(details["ai_prediction_type"], "value") else details["ai_prediction_type"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch review details: {str(e)}"
        )

@router.post("/{prediction_id}/submit", response_model=AgentPredictionResponse)
async def submit_review(
    prediction_id: int, 
    request: ReviewSubmitRequest, 
    db: Session = Depends(get_db)
):
    """Process HR feedback on a specific prediction."""
    try:
        service = get_review_service(db)
        entity = await service.submit_review(
            prediction_id=prediction_id,
            is_correct=request.is_correct,
            hr_notes=request.hr_notes
        )
        
        db.commit()
        
        return AgentPredictionResponse(
            id=entity.id,
            daily_log_id=entity.daily_log_id,
            burnout_risk=entity.burnout_risk,
            burnout_rate=entity.burnout_rate,
            confidence_score=entity.confidence_score,
            confidence_percentage=entity.get_confidence_percentage(),
            created_at=entity.created_at
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {str(e)}"
        )
@router.post("/test-email")
async def test_email_service():
    """Simple endpoint to test the email service configuration."""
    try:
        email_service = get_email_service()
        success = await email_service.send_email(
            to=["emin.brankovic19@gmail.com"],
            subject="🚀 Test Email - Burnout Prevention System",
            body_html="""
            <h3>System Test</h3>
            <p>If you are reading this, the email service is correctly configured and functional!</p>
            <hr>
            <p>Sent via SMTP (smtp.gmail.com:587)</p>
            """
        )
        
        if success:
            return {"status": "success", "message": "Test email sent successfully to lednacar@gmail.com"}
        else:
            return {"status": "error", "message": "Failed to send email. Check console logs for errors."}
            
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email test failed: {str(e)}"
        )
