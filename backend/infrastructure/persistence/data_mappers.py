from backend.domain.entities.employee import EmployeeEntity
from backend.domain.entities.department import DepartmentEntity
from backend.domain.entities.daily_log import DailyLogEntity

from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.domain.entities.system_settings import SystemSettingsEntity
from backend.domain.entities.model_version import ModelVersionEntity
from backend.domain.enums.enums import DailyLogStatus
from backend.infrastructure.persistence.database import Employee, Department, DailyLog, AgentPrediction, SystemSettings, ModelVersion



# Department Mappers
def department_model_to_entity(model: Department) -> DepartmentEntity:
    """Convert SQLAlchemy Department model to domain entity."""
    return DepartmentEntity(
        id=model.id,
        name=model.name,
        description=model.description,
        created_at=model.created_at
    )


def department_entity_to_model(entity: DepartmentEntity) -> Department:
    """Convert domain entity to SQLAlchemy Department model."""
    return Department(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at
    )


# Employee Mappers
def employee_model_to_entity(model: Employee) -> EmployeeEntity:
    """Convert SQLAlchemy Employee model to domain entity."""
    return EmployeeEntity(
        id=model.id,
        first_name=model.first_name,
        last_name=model.last_name,
        email=model.email,
        department_id=model.department_id,
        hire_date=model.hire_date,
        high_burnout_streak=model.high_burnout_streak if hasattr(model, 'high_burnout_streak') else 0,
        last_alert_sent=model.last_alert_sent if hasattr(model, 'last_alert_sent') else None
    )


def employee_entity_to_model(entity: EmployeeEntity) -> Employee:
    """Convert domain entity to SQLAlchemy Employee model."""
    return Employee(
        id=entity.id,
        first_name=entity.first_name,
        last_name=entity.last_name,
        email=entity.email,
        department_id=entity.department_id,
        hire_date=entity.hire_date,
        high_burnout_streak=entity.high_burnout_streak,
        last_alert_sent=entity.last_alert_sent
    )


# DailyLog Mappers
def daily_log_model_to_entity(model: DailyLog) -> DailyLogEntity:
    """
    Convert SQLAlchemy DailyLog model to domain entity.

    Args:
        model: DailyLog ORM model from database

    Returns:
        DailyLogEntity: Pure domain entity
    """
    return DailyLogEntity(
        id=model.id,
        employee_id=model.employee_id,
        log_date=model.log_date,
        hours_worked=model.hours_worked,
        hours_slept=model.hours_slept,
        daily_personal_time=model.daily_personal_time,
        motivation_level=model.motivation_level,
        stress_level=model.stress_level,
        workload_intensity=model.workload_intensity,
        overtime_hours_today=model.overtime_hours_today,
        status=DailyLogStatus(model.status) if model.status else DailyLogStatus.PENDING,
        processed_at=model.processed_at
    )


def daily_log_entity_to_model(entity: DailyLogEntity) -> DailyLog:
    """
    Convert domain entity to SQLAlchemy DailyLog model.

    Args:
        entity: DailyLogEntity from domain layer

    Returns:
        DailyLog: SQLAlchemy ORM model ready for persistence
    """
    return DailyLog(
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
        status=entity.status.value,  # Convert enum to string
        processed_at=entity.processed_at
    )


# AgentPrediction Mappers
def agent_prediction_model_to_entity(model: AgentPrediction) -> AgentPredictionEntity:
    """Convert SQLAlchemy AgentPrediction model to domain entity."""
    return AgentPredictionEntity(
        id=model.id,
        daily_log_id=model.daily_log_id,
        burnout_risk=model.burnout_risk,
        burnout_rate=model.burnout_rate,
        confidence_score=model.confidence_score,
        created_at=model.created_at,
        needs_review=model.needs_review,
        human_validation=model.human_validation,
        review_notes=model.review_notes,
        reviewed_at=model.reviewed_at,
        model_version=model.model_version
    )


def agent_prediction_entity_to_model(entity: AgentPredictionEntity) -> AgentPrediction:
    """Convert domain entity to SQLAlchemy AgentPrediction model."""
    return AgentPrediction(
        id=entity.id,
        daily_log_id=entity.daily_log_id,
        burnout_risk=entity.burnout_risk,
        burnout_rate=entity.burnout_rate,
        confidence_score=entity.confidence_score,
        created_at=entity.created_at,
        needs_review=entity.needs_review,
        human_validation=entity.human_validation,
        review_notes=entity.review_notes,
        reviewed_at=entity.reviewed_at,
        model_version=entity.model_version
    )


# SystemSettings Mappers
def system_settings_model_to_entity(model: SystemSettings) -> SystemSettingsEntity:
    """Convert SQLAlchemy SystemSettings model to domain entity."""
    return SystemSettingsEntity(
        id=model.id,
        new_samples_count=model.new_samples_count,
        retrain_threshold=model.retrain_threshold,
        auto_retrain_enabled=model.auto_retrain_enabled,
        last_retrain_at=model.last_retrain_at,
        retrain_count=model.retrain_count
    )


def system_settings_entity_to_model(entity: SystemSettingsEntity) -> SystemSettings:
    """Convert domain entity to SQLAlchemy SystemSettings model."""
    return SystemSettings(
        id=entity.id,
        new_samples_count=entity.new_samples_count,
        retrain_threshold=entity.retrain_threshold,
        auto_retrain_enabled=entity.auto_retrain_enabled,
        last_retrain_at=entity.last_retrain_at,
        retrain_count=entity.retrain_count
    )


# ModelVersion Mappers
def model_version_model_to_entity(model: ModelVersion) -> ModelVersionEntity:
    """Convert SQLAlchemy ModelVersion model to domain entity."""
    return ModelVersionEntity(
        id=model.id,
        version_number=model.version_number,
        training_mode=model.training_mode,
        dataset_size=model.dataset_size,
        accuracy=model.accuracy,
        model_file_path=model.model_file_path,
        created_at=model.created_at
    )


def model_version_entity_to_model(entity: ModelVersionEntity) -> ModelVersion:
    """Convert domain entity to SQLAlchemy ModelVersion model."""
    return ModelVersion(
        id=entity.id,
        version_number=entity.version_number,
        training_mode=entity.training_mode,
        dataset_size=entity.dataset_size,
        accuracy=entity.accuracy,
        model_file_path=entity.model_file_path,
        created_at=entity.created_at
    )

