import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.new_model import MODEL_PATH, load_trained_model, train_model
from infrastructure.persistence.database import init_db
from presentation.api import (
    employee_routes,
    department_routes,
    daily_log_routes,
    agent_prediction_routes
)

import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Employee Management & Burnout Prediction API",
    version="1.0.0",
    description="Clean Architecture API for employee management with AI-powered burnout predictions"
)

# CORS middleware (if you have a frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
# @app.on_event("startup")
# def on_startup():
#     def load_or_train_model():
#         if os.path.exists(MODEL_PATH):
#             load_trained_model()
#         else:
#             print("No model found. Training new model...")
#             train_model()
#             print("Model trained.")
#             load_trained_model()
#
#     """Create database tables on startup."""
#     init_db()
#     print("Database initialized successfully!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting up...")

    # Load or train model
    if os.path.exists(MODEL_PATH):
        load_trained_model()
        print("✅ Model loaded successfully!")
    else:
        print("⚠️ No model found. Training new model...")
        train_model()
        print("✅ Model trained successfully!")
        load_trained_model()
    # Initialize database
    init_db()
    print("✅ Database initialized successfully!")



    yield  # Application runs here

    # Shutdown (optional cleanup)
    print("👋 Shutting down...")

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
