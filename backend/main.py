import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.application.services.training_service import get_training_service
from backend.infrastructure.persistence.databse_seeder import run_seeder
from backend.services.new_model import MODEL_PATH, load_trained_model, train_model
from infrastructure.persistence.database import init_db, check_database_exists
from presentation.api import (
    employee_routes,
    department_routes,
    daily_log_routes,
    agent_prediction_routes
)

import uvicorn

# Create FastAPI app

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""

    print("=" * 80)
    print("🚀 STARTING APPLICATION")
    print("=" * 80)

    # ========== DATABASE INITIALIZATION ==========
    print("\n📊 Step 1: Database Initialization")
    print("-" * 80)

    # Initialize database (create tables)
    init_db()

    # Check if database needs seeding
    if not check_database_exists():
        print("\n📂 Database is empty - seeding with initial data...")
        run_seeder()
    else:
        print("\n✅ Database already contains data - skipping seed")

    # ========== ML MODEL INITIALIZATION ==========
    print("\n🤖 Step 2: ML Model Initialization")
    print("-" * 80)

    if os.path.exists(MODEL_PATH):
        print(f"✅ Model found at {MODEL_PATH}")
        print("   Loading model...")
        training_service = get_training_service()
        training_service.predictor.load_model(MODEL_PATH)
        print("✅ Model loaded successfully!")
    else:
        print(f"⚠️  No model found at {MODEL_PATH}")
        print("   Training new model...")
        training_service = get_training_service()
        model_path, metrics = await training_service.train_model()
        print(f"\n✅ Model trained and saved to {model_path}")
        print(f"   📊 Metrics:")
        print(f"      - Train R²: {metrics.train_r2_score:.4f}")
        print(f"      - Test R²: {metrics.test_r2_score:.4f}")
        print(f"      - MAE: {metrics.mae:.4f}")

    # ========== STARTUP COMPLETE ==========
    print("\n" + "=" * 80)
    print("✅ APPLICATION READY!")
    print("=" * 80)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔄 ReDoc: http://localhost:8000/redoc")
    print("💚 Health Check: http://localhost:8000/health")
    print("=" * 80 + "\n")

    yield  # Application runs here

    # ========== SHUTDOWN ==========
    print("\n" + "=" * 80)
    print("👋 Shutting down...")
    print("=" * 80)


app = FastAPI(
    title="Employee Management & Burnout Prediction API",
    version="1.0.0",
    description="Clean Architecture API for employee management with AI-powered burnout predictions",
    lifespan=lifespan
)

# CORS middleware (if you have a frontend)
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

# Root endpoint
@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Employee Management & Burnout Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True,log_level="debug" )
