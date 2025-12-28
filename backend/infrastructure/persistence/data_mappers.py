from backend.domain.entities.employee import EmployeeEntity
from backend.domain.entities.department import DepartmentEntity
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.entities.agent_prediction import AgentPredictionEntity
from backend.infrastructure.persistence.models import Employee, Department, DailyLog, AgentPrediction


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
        hire_date=model.hire_date
    )


def employee_entity_to_model(entity: EmployeeEntity) -> Employee:
    """Convert domain entity to SQLAlchemy Employee model."""
    return Employee(
        id=entity.id,
        first_name=entity.first_name,
        last_name=entity.last_name,
        email=entity.email,
        department_id=entity.department_id,
        hire_date=entity.hire_date
    )


# DailyLog Mappers
def daily_log_model_to_entity(model: DailyLog) -> DailyLogEntity:
    """Convert SQLAlchemy DailyLog model to domain entity."""
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
        overtime_hours_today=model.overtime_hours_today
    )


def daily_log_entity_to_model(entity: DailyLogEntity) -> DailyLog:
    """Convert domain entity to SQLAlchemy DailyLog model."""
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
        overtime_hours_today=entity.overtime_hours_today
    )


# AgentPrediction Mappers
def agent_prediction_model_to_entity(model: AgentPrediction) -> AgentPredictionEntity:
    """Convert SQLAlchemy AgentPrediction model to domain entity."""
    return AgentPredictionEntity(
        id=model.id,
        daily_log_id=model.daily_log_id,
        prediction_type=model.prediction_type,
        prediction_value=model.prediction_value,
        confidence_score=model.confidence_score,
        created_at=model.created_at
    )


def agent_prediction_entity_to_model(entity: AgentPredictionEntity) -> AgentPrediction:
    """Convert domain entity to SQLAlchemy AgentPrediction model."""
    return AgentPrediction(
        id=entity.id,
        daily_log_id=entity.daily_log_id,
        prediction_type=entity.prediction_type,
        prediction_value=entity.prediction_value,
        confidence_score=entity.confidence_score,
        created_at=entity.created_at
    )
