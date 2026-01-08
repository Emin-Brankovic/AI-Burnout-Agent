import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.application.services.training_service import get_training_service
from backend.infrastructure.persistence.databse_seeder import run_seeder
from backend.services.new_model import MODEL_PATH
from backend.infrastructure.persistence.database import init_db, check_database_exists, SessionLocal
from backend.web.workers.burnout_prediction_worker import BurnoutPredictionWorker
from backend.application.services.prediction_service import get_prediction_service
from backend.application.services.email_service import get_email_notification_service
from backend.presentation.api import (
    employee_routes,
    department_routes,
    daily_log_routes,
    agent_prediction_routes,
    review_routes,
    dashboard_routes
)
from backend.application.services.review_service import get_review_service

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
    print("BURNOUT DETECTION SYSTEM STARTING")
    print("=" * 80)

    # ========== 1 & 2: DATABASE & ML INITIALIZATION ==========
    # Ensure all tables exist (safe to run on existing DB)
    init_db()

    # Only run seeder if the main data tables are empty
    if not check_database_exists():
        run_seeder()
    
    app_state.training_service = get_training_service()
    if os.path.exists(MODEL_PATH):
        app_state.training_service.predictor.load_model(MODEL_PATH)

    # ========== 4/6: SERVICES INITIALIZATION ==========
    print("\nStep 4: Creating services...")
    # Creating fresh database sessions for thread safety in workers
    db_session = app_state.db_session_factory()
    
    # Initialize your core business services
    # Note: Replace these with your actual Service class initializations
    app_state.prediction_service = get_prediction_service(db_session)
    app_state.notification_service = get_email_notification_service()
    app_state.review_service = get_review_service(db_session)
    
    # The Review Service we built earlier

    


    # ========== 5/6: AGENT RUNNERS ==========
    print("\nStep 5: Creating agent runners...")
    # The "Runner" contains the Sense-Think-Act logic
    from backend.application.agents.burnout_prediction_agent_runner import BurnoutPredictionAgentRunner
    
    app_state.prediction_runner = BurnoutPredictionAgentRunner(
        queue_service=app_state.prediction_service.queue_service,
        prediction_service=app_state.prediction_service,
        email_notification_service=app_state.notification_service,
        name="BurnoutPredictionAgent"
    )

    # ========== 6/6: BACKGROUND WORKERS ==========
    print("\nStep 6: Starting background workers...")
    
    # A. Scoped Session Factory for Thread-Safe Singleton Access
    from sqlalchemy.orm import scoped_session
    from backend.infrastructure.persistence.database import SessionLocal
    from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
    from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
    from backend.ML.burnout_predictor import BurnoutPredictor
    
    # Create a thread-local session factory. 
    # Any usage of this proxy object in a thread gets a dedicated session.
    ThreadLocalSession = scoped_session(SessionLocal)
    
    def model_factory():
        """
        Creates a BurnoutPredictor that uses thread-local DB sessions.
        Safe to be held as a singleton in ModelRegistry.
        """
        # Pass the scoped_session proxy as the 'session' argument
        # Repositories will blindly call .query() on it, which delegates to thread-local session
        d_repo = DailyLogRepository(ThreadLocalSession)
        e_repo = EmployeeRepository(ThreadLocalSession)
        
        # Determine strict model path model_path or default
        model_path = 'backend/ml_models/burnout_model.pkl'
        
        pred = BurnoutPredictor(daily_log_repo=d_repo, employee_repo=e_repo)
        
        # Load weights if available
        if os.path.exists(model_path):
             pred.load_model(model_path)
             
        return pred

    # B. Initialize ModelRegistry with initial model
    from backend.application.services.model_registry import ModelRegistry
    registry = ModelRegistry()
    if not registry.active_model:
        print("   Loading initial model into Registry...")
        try:
            initial_model = model_factory()
            registry.load_new_model(initial_model)
        except Exception as e:
             print(f"   Failed to load initial model: {e}")

    # C. Start Prediction Worker (Queue Processor)
    from backend.web.workers.burnout_prediction_worker import BurnoutPredictionWorker
    
    app_state.prediction_worker = BurnoutPredictionWorker(
        runner=app_state.prediction_runner,
        tick_interval_seconds=5,
        name="BurnoutWorker"
    )
    app_state.prediction_worker.start()

    # D. Start Learning Worker (Self-Improvement Loop)
    from backend.web.workers.learning_worker import LearningWorker
    
    # We use the training service as the ITrainer implementation
    app_state.learning_worker = LearningWorker(
        interval_seconds=60, # Check for retraining every minute
        trainer=app_state.training_service,
        model_factory=model_factory
    )
    app_state.learning_worker.start()

    print("\n" + "=" * 80)
    print("APPLICATION READY!")
    print("=" * 80)

    yield  # --- Application is running ---

    # ========== SHUTDOWN ==========
    print("\nShutting down...")
    
    if app_state.prediction_worker:
        app_state.prediction_worker.stop()
        
    if hasattr(app_state, 'learning_worker') and app_state.learning_worker:
        app_state.learning_worker.stop()
        
    db_session.close()
    ThreadLocalSession.remove() # Clean up thread-local sessions
    print("Shutdown complete")


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
app.include_router(dashboard_routes.router, prefix="/api")

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
