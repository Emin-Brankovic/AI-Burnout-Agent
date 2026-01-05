import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.application.services.training_service import get_training_service
from backend.infrastructure.persistence.databse_seeder import run_seeder
from backend.services.new_model import MODEL_PATH
from backend.infrastructure.persistence.database import init_db, check_database_exists, SessionLocal
from backend.web.workers.burnout_prediction_worker import BurnoutPredictionWorker, get_prediction_worker
from backend.application.services.prediction_service import get_prediction_service
from backend.application.services.email_service import get_email_notification_service

from backend.presentation.api import (
    employee_routes,
    department_routes,
    daily_log_routes,
    agent_prediction_routes,
    review_routes
)

class AppState:
    """Global application state"""
    
    def __init__(self):
        # Infrastructure
        self.db_session_factory = SessionLocal
        
        # Workers
        self.prediction_worker: BurnoutPredictionWorker = None
        
        # Services
        self.training_service = None

app_state = AppState()

# ========================================
# LIFECYCLE
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""

    print("=" * 80)
    print("🚀 BURNOUT DETECTION SYSTEM STARTING")
    print("=" * 80)

    # ========== 1 & 2: DATABASE & ML INITIALIZATION ==========
    # (Keeping your existing logic for init_db and model loading...)
    if not check_database_exists():
        init_db()
        run_seeder()
    
    app_state.training_service = get_training_service()
    if os.path.exists(MODEL_PATH):
        app_state.training_service.predictor.load_model(MODEL_PATH)

    # ========== 4/6: SERVICES INITIALIZATION ==========
    print("\n⚙️  Step 4: Creating services...")
    # Creating fresh database sessions for thread safety in workers
    db_session = app_state.db_session_factory()
    
    # Initialize your core business services
    # Note: Replace these with your actual Service class initializations
    app_state.prediction_service = get_prediction_service(db_session)
    app_state.notification_service = get_email_notification_service()
    
    # The Review Service we built earlier
    from backend.application.services.review_service import ReviewService
    from backend.application.helpers.agent_policy_helper import AgentPolicyHelper
    
    policy_helper = AgentPolicyHelper(
        daily_log_repository=app_state.prediction_service.daily_log_repository,
        prediction_repository=app_state.prediction_service.prediction_repository
    )
    
    app_state.review_service = ReviewService(
        prediction_repository=app_state.prediction_service.prediction_repository,
        daily_log_repository=app_state.prediction_service.daily_log_repository,
        employee_repository=app_state.prediction_service.employee_repository,
        policy_helper=policy_helper,
        notification_service=app_state.notification_service
    )

    # ========== 5/6: AGENT RUNNERS ==========
    print("\n🤖 Step 5: Creating agent runners...")
    # The "Runner" contains the Sense-Think-Act logic
    from backend.application.agents.burnout_prediction_agent_runner import BurnoutPredictionAgentRunner
    
    app_state.prediction_runner = BurnoutPredictionAgentRunner(
        queue_service=app_state.prediction_service.queue_service,
        prediction_service=app_state.prediction_service,
        email_notification_service=app_state.notification_service,
        name="BurnoutPredictionAgent"
    )

    # ========== 6/6: BACKGROUND WORKERS ==========
    print("\n🔄 Step 6: Starting background workers...")
    # The "Worker" is the thread that keeps the Runner ticking
    from backend.web.workers.burnout_prediction_worker import BurnoutPredictionWorker
    
    app_state.prediction_worker = BurnoutPredictionWorker(
        runner=app_state.prediction_runner,
        tick_interval_seconds=5,
        name="BurnoutWorker"
    )
    app_state.prediction_worker.start()

    print("\n" + "=" * 80)
    print("✅ APPLICATION READY!")
    print("=" * 80)

    yield  # --- Application is running ---

    # ========== SHUTDOWN ==========
    print("\n🛑 Shutting down...")
    if app_state.prediction_worker:
        app_state.prediction_worker.stop()
    db_session.close()
    print("✅ Shutdown complete")


app = FastAPI(
    title="Employee Management & Burnout Prediction API",
    version="1.0.0",
    description="Clean Architecture API for employee management with AI-powered burnout predictions",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include all routers
app.include_router(employee_routes.router, prefix="/api")
app.include_router(department_routes.router, prefix="/api")
app.include_router(daily_log_routes.router, prefix="/api")
app.include_router(agent_prediction_routes.router, prefix="/api")
app.include_router(review_routes.router, prefix="/api")

# Root endpoint
@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Employee Management & Burnout Prediction API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "worker_running": app_state.prediction_worker.is_running if app_state.prediction_worker else False
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True, log_level="debug")
