from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.application.services.base_crud_service import BaseCRUDService
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.enums.enums import DailyLogStatus
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository


class DailyLogService(BaseCRUDService[
                          DailyLogEntity,
                          DailyLogRepositoryInterface,
                          Dict[str, Any],
                          Dict[str, Any]
                      ]):
    """DailyLog service with CRUD operations."""

    def __init__(self, session: Session):
        repository = DailyLogRepository(session)
        super().__init__(session, repository)
        self.prediction_repo = AgentPredictionRepository(session)

    def map_insert_to_entity(self, request: Dict[str, Any]) -> DailyLogEntity:
        """Map insert request to DailyLogEntity."""
        return DailyLogEntity(
            employee_id=request.employee_id,
            log_date=request.log_date or datetime.now(),
            hours_worked=request.hours_worked,
            hours_slept=request.hours_slept,
            daily_personal_time=request.daily_personal_time,
            motivation_level=request.motivation_level,
            stress_level=request.stress_level,
            workload_intensity=request.workload_intensity,
            overtime_hours_today=request.overtime_hours_today,
        )
    def map_update_to_entity(
            self,
            entity: DailyLogEntity,
            request: Dict[str, Any]
    ) -> DailyLogEntity:
        """Map update request to DailyLogEntity."""
        if 'log_date' in request:
            entity.log_date = request['log_date']
        if 'hours_worked' in request:
            entity.hours_worked = request['hours_worked']
        if 'hours_slept' in request:
            entity.hours_slept = request['hours_slept']
        if 'daily_personal_time' in request:
            entity.daily_personal_time = request['daily_personal_time']
        if 'motivation_level' in request:
            entity.motivation_level = request['motivation_level']
        if 'stress_level' in request:
            entity.stress_level = request['stress_level']
        if 'workload_intensity' in request:
            entity.workload_intensity = request['workload_intensity']
        if 'overtime_hours_today' in request:
            entity.overtime_hours_today = request['overtime_hours_today']

        return entity

    def get_by_employee(self, employee_id: int) -> List[DailyLogEntity]:
        """Get all logs for an employee."""
        return self.repository.get_by_employee(employee_id)

    def get_by_date_range(
            self,
            employee_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> List[DailyLogEntity]:
        """Get logs for employee within date range."""
        return self.repository.get_by_date_range(employee_id, start_date, end_date)

    def get_log_and_subsequent(self, log_id: int) -> List[Dict[str, Any]]:
        """
        Get specific log and 7 subsequent logs with prediction details.
        Total 8 logs.
        """
        # 1. Get the target log
        target_log = self.repository.get_by_id(log_id)
        if not target_log:
            raise ValueError(f"Daily log {log_id} not found")

        # 2. Get all logs for employee (they come ordered by date desc usually, but we check impl)
        # DailyLogRepository.get_by_employee orders by log_date DESC
        all_logs = self.repository.get_by_employee(target_log.employee_id)

        # 3. Filter: logs with date >= target_log.date
        # We need ascending order to pick the next ones easily
        subsequent_logs = [
            log for log in all_logs
            if log.log_date >= target_log.log_date
        ]
        
        # Sort ascending (oldest first) so we get [target, target+1d, target+2d...]
        subsequent_logs.sort(key=lambda x: x.log_date)

        # 4. Take target + 7 next = 8 total
        selected_logs = subsequent_logs[:8]

        result = []
        for log in selected_logs:
            # 5. Fetch prediction
            preds = self.prediction_repo.get_by_daily_log(log.id)
            latest_pred = preds[0] if preds else None
            
            # 6. Construct response dict (matches schema structure roughly, but is dict for flexibility)
            # We will use the schema in the router to serialize
            log_dict = log.__dict__.copy() # simplistic, better to be explicit or use schema dump
            
            # Adding prediction data
            log_dict["burnout_risk"] = latest_pred.burnout_risk if latest_pred else None
            log_dict["burnout_rate"] = latest_pred.burnout_rate if latest_pred else None
            log_dict["confidence_score"] = latest_pred.confidence_score if latest_pred else None
            
            result.append(log_dict)

        return result

    def generate_random_logs(self, batch_size: int) -> tuple[List[DailyLogEntity], int]:
        """
        Generate random daily logs with realistic values and enqueue them for prediction.
        
        This method:
        1. Validates batch_size
        2. Retrieves all employees from database
        3. Generates random daily logs with constrained values
        4. Saves them to database with QUEUED status
        5. Returns the generated logs
        
        Args:
            batch_size: Number of random logs to generate
            
        Returns:
            Tuple of (list of generated entities, requested count)
            
        Raises:
            ValueError: If batch_size is invalid or no employees exist
            Exception: If database operation fails
        """
        import random
        from datetime import datetime, timedelta
        from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
        
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        
        try:
            # Get all employees to randomly assign logs
            employee_repo = EmployeeRepository(self.session)
            all_employees = employee_repo.get_all()
            
            if not all_employees:
                raise ValueError("No employees found in database. Please create employees first.")
            
            employee_ids = [emp.id for emp in all_employees]
            
            generated_logs = []
            
            # Define realistic value ranges for each field
            for i in range(batch_size):
                # Random employee
                employee_id = random.choice(employee_ids)
                
                # Random date within last 90 days
                days_ago = random.randint(0, 90)
                log_date = datetime.now() - timedelta(days=days_ago)
                
                # Generate realistic random values with weighted distributions
                # Hours worked: mostly 6-10, occasionally more
                hours_worked = round(random.triangular(6, 12, 8), 1)
                
                # Hours slept: mostly 6-8, some less, some more
                hours_slept = round(random.triangular(4, 9, 7), 1)
                
                # Personal time: 0-4 hours
                daily_personal_time = round(random.triangular(0, 4, 1.5), 1)
                
                # Motivation level: 1-10, weighted toward middle
                motivation_level = random.choices(
                    range(1, 11),
                    weights=[5, 8, 12, 15, 20, 20, 15, 12, 8, 5]
                )[0]
                
                # Stress level: 1-10, weighted toward middle-high
                stress_level = random.choices(
                    range(1, 11),
                    weights=[5, 8, 10, 12, 15, 18, 15, 10, 5, 2]
                )[0]
                
                # Workload intensity: 1-10, weighted toward middle-high
                workload_intensity = random.choices(
                    range(1, 11),
                    weights=[5, 8, 10, 12, 15, 18, 15, 10, 5, 2]
                )[0]
                
                # Overtime hours: mostly 0-2, occasionally more
                overtime_hours_today = round(random.triangular(0, 4, 0.5), 1)
                
                # Create entity
                log_entity = DailyLogEntity(
                    employee_id=employee_id,
                    log_date=log_date,
                    hours_worked=hours_worked,
                    hours_slept=hours_slept,
                    daily_personal_time=daily_personal_time,
                    motivation_level=motivation_level,
                    stress_level=stress_level,
                    workload_intensity=workload_intensity,
                    overtime_hours_today=overtime_hours_today,
                    status=DailyLogStatus.QUEUED  # Automatically enqueue for prediction
                )
                
                generated_logs.append(log_entity)
            
            # Save all to database in batch
            generated_logs = self.repository.add_many(generated_logs)

            # Commit all at once
            self.session.commit()
            
            print(f"Generated and enqueued {len(generated_logs)} random daily logs")
            
            return generated_logs, batch_size
            
        except Exception as e:
            self.session.rollback()
            print(f"Random log generation failed: {e}")
            raise


