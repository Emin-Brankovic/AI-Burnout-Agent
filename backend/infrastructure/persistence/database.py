import os
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, inspect, text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from typing import List, Optional
from backend.domain.enums.enums import DailyLogStatus

# Get absolute path to backend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Goes up 3 levels to backend/
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "app.db"

# Ensure data directory exists
DATABASE_DIR.mkdir(exist_ok=True)

# Database URL with absolute path
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

print(f"Database directory: {DATABASE_DIR}")
print(f"Database path: {DATABASE_PATH}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to False in production
)

# Enable WAL mode for SQLite to improve concurrency
# from sqlalchemy import event

# @event.listens_for(engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA journal_mode=WAL")
#     cursor.execute("PRAGMA synchronous=NORMAL")
#     cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==================== MODELS ====================

class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    job_title = Column(String(100), nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)
    salary = Column(Float, nullable=True)
    high_burnout_streak = Column(Integer, nullable=False, default=0)
    last_alert_sent = Column(DateTime, nullable=True)

    department = relationship("Department", back_populates="employees")
    daily_logs = relationship("DailyLog", back_populates="employee")


class DailyLog(Base):
    __tablename__ = 'daily_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    log_date = Column(DateTime, nullable=False)
    hours_worked = Column(Float, nullable=True)
    hours_slept = Column(Float, nullable=True)
    daily_personal_time = Column(Float, nullable=True)
    motivation_level = Column(Integer, nullable=True)
    stress_level = Column(Integer, nullable=True)
    workload_intensity = Column(Integer, nullable=True)
    overtime_hours_today = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default=DailyLogStatus.QUEUED)
    processed_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="daily_logs")
    agent_predictions = relationship("AgentPrediction", back_populates="daily_log")


class AgentPrediction(Base):
    __tablename__ = 'agent_predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_log_id = Column(Integer, ForeignKey('daily_logs.id'), nullable=False)
    burnout_risk = Column(String(50), nullable=False)
    burnout_rate = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False)
    human_validation = Column(Boolean, nullable=True) #NULL = Not reviewed, True = AI was right, False = AI was wrong
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)


    daily_log = relationship("DailyLog", back_populates="agent_predictions")


class SystemSettings(Base):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True, default=1)
    new_samples_count = Column(Integer, default=0, nullable=False)
    retrain_threshold = Column(Integer, default=100, nullable=False)
    auto_retrain_enabled = Column(Boolean, default=True, nullable=False)
    last_retrain_at = Column(DateTime, nullable=True)
    retrain_count = Column(Integer, default=0, nullable=False)


class ModelVersion(Base):
    __tablename__ = 'model_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_number = Column(String(50), nullable=False, unique=True)
    training_mode = Column(String(50), nullable=False)
    dataset_size = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=True)
    model_file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



# ==================== UTILITIES ====================

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    print("🔍 Initializing database...")
    print(f"   Tables to create: {list(Base.metadata.tables.keys())}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print(f"✅ Database initialized at: {DATABASE_PATH}")
    print(f"   Created tables: {list(Base.metadata.tables.keys())}")

def check_database_exists() -> bool:
    """
    Check if database exists and has data.

    Returns:
        bool: True if database has data, False otherwise
    """
    try:
        # Check if database file exists
        if not DATABASE_PATH.exists():
            print("   📂 Database file does not exist")
            return False

        # Check if tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            print("   📂 No tables found in database")
            return False

        # Check if there's data in departments table
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT COUNT(*) FROM departments")).scalar()
            has_data = result > 0

            if has_data:
                print(f"   ✅ Database exists with {result} departments")
            else:
                print("   📂 Database exists but is empty")

            return has_data
        finally:
            db.close()

    except Exception as e:
        print(f"   ⚠️ Database check error: {e}")
        return False
