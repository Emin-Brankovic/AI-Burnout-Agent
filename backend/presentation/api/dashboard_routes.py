from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.infrastructure.persistence.database import get_db
from backend.application.services.dashboard_service import DashboardService
from backend.presentation.schemas.dashboard_schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    page: int = 1,
    page_size: int = 10,
    department: str | None = None,
    status: str | None = None,
    trend: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview data including summary statistics and employee list.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    - department: Filter by department name (optional)
    - status: Filter by burnout risk status (optional)
    - trend: Filter by trend (increasing/decreasing/stable) (optional)
    """
    try:
        service = DashboardService(db)
        return service.get_dashboard_data(
            page=page, 
            page_size=page_size,
            department=department,
            status=status,
            trend=trend
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}"
        )
