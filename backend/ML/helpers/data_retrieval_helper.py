"""
Data retrieval utilities for burnout prediction.
Refactored to use existing repository pattern instead of duplicating database logic.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.domain.repositories_interfaces.employee_repository_interface import EmployeeRepositoryInterface


class DataRetriever:
    """
    Handles data retrieval using existing repositories.
    No direct database queries - delegates to repository layer.
    """

    # Default fallback values
    DEFAULT_VALUES = {
        'Work_Hours_Per_Day': 8.0,
        'Sleep_Hours_Per_Night': 7.0,
        'Personal_Time_Hours_Per_Day': 2.0,
        'Motivation_Level': 5,
        'Work_Stress_Level': 5,
        'Workload_Intensity': 5,
        'Overtime_Hours_Today': 0.0
    }

    def __init__(
        self,
        daily_log_repository: Optional[DailyLogRepositoryInterface] = None,
        employee_repository: Optional[EmployeeRepositoryInterface] = None
    ):
        """
        Initialize data retriever with repository dependencies.

        Args:
            daily_log_repository: Repository for daily log operations
            employee_repository: Repository for employee operations
        """
        self.daily_log_repo = daily_log_repository
        self.employee_repo = employee_repository

        # Caches for performance
        self._department_averages_cache: Dict[int, Dict[str, float]] = {}
        self._global_averages_cache: Optional[Dict[str, float]] = None

    def set_repositories(
        self,
        daily_log_repository: DailyLogRepositoryInterface,
        employee_repository: EmployeeRepositoryInterface
    ):
        """Set repository dependencies."""
        self.daily_log_repo = daily_log_repository
        self.employee_repo = employee_repository

    # ========== HELPER: ENTITY TO DICT ==========

    def _entity_to_dict(self, entity: DailyLogEntity) -> Dict[str, float]:
        """Convert DailyLogEntity to feature dictionary."""
        return {
            'Employee_ID': entity.employee_id,
            'Work_Hours_Per_Day': entity.hours_worked or 8.0,
            'Sleep_Hours_Per_Night': entity.hours_slept or 7.0,
            'Personal_Time_Hours_Per_Day': entity.daily_personal_time or 2.0,
            'Motivation_Level': entity.motivation_level or 5,
            'Work_Stress_Level': entity.stress_level or 5,
            'Workload_Intensity': entity.workload_intensity or 5,
            'Overtime_Hours_Today': entity.overtime_hours_today or 0.0
        }

    # ========== DATA RETRIEVAL METHODS ==========

    def get_historical_logs(self, employee_id: int, limit: int = 6) -> pd.DataFrame:
        """
        Retrieve historical daily logs using repository.

        Args:
            employee_id: Employee ID
            limit: Number of historical records to fetch

        Returns:
            DataFrame with historical logs
        """
        if self.daily_log_repo is None:
            print("⚠️ No daily log repository available")
            return pd.DataFrame()

        try:
            # Use repository method instead of direct query
            all_logs = self.daily_log_repo.get_by_employee(employee_id)

            if not all_logs:
                print(f"⚠️ No historical logs found for employee {employee_id}")
                return pd.DataFrame()

            # Sort by date descending and take limit
            # Note: repository already returns sorted by date desc
            recent_logs = all_logs[:limit]

            # Convert entities to dictionaries
            data = [self._entity_to_dict(log) for log in reversed(recent_logs)]

            df = pd.DataFrame(data)
            print(f"✅ Retrieved {len(df)} historical logs for employee {employee_id}")
            return df

        except Exception as e:
            print(f"❌ Error fetching historical logs: {e}")
            return pd.DataFrame()

    def get_department_averages(self, department_id: int) -> Dict[str, float]:
        """
        Get average feature values for employees in department.
        Results are cached for performance.

        Args:
            department_id: Department ID

        Returns:
            Dictionary of average feature values
        """
        if self.daily_log_repo is None or self.employee_repo is None:
            return self.DEFAULT_VALUES.copy()

        # Check cache
        if department_id in self._department_averages_cache:
            print(f"✅ Using cached department {department_id} averages")
            return self._department_averages_cache[department_id]

        try:
            # Get all employees in department using repository
            employees = self.employee_repo.get_by_department(department_id)

            if not employees:
                print(f"⚠️ No employees found in department {department_id}")
                return self.DEFAULT_VALUES.copy()

            # Get logs for all employees in department (last 500 total)
            all_logs: List[DailyLogEntity] = []
            logs_per_employee = max(1, 500 // len(employees))  # Distribute 500 across employees

            for employee in employees:
                employee_logs = self.daily_log_repo.get_by_employee(employee.id)
                all_logs.extend(employee_logs[:logs_per_employee])

                if len(all_logs) >= 500:
                    break

            if not all_logs:
                print(f"⚠️ No logs found for department {department_id}")
                return self.DEFAULT_VALUES.copy()

            # Calculate averages from entities
            averages = {
                'Work_Hours_Per_Day': np.mean([log.hours_worked or 8.0 for log in all_logs]),
                'Sleep_Hours_Per_Night': np.mean([log.hours_slept or 7.0 for log in all_logs]),
                'Personal_Time_Hours_Per_Day': np.mean([log.daily_personal_time or 2.0 for log in all_logs]),
                'Motivation_Level': int(np.mean([log.motivation_level or 5 for log in all_logs])),
                'Work_Stress_Level': int(np.mean([log.stress_level or 5 for log in all_logs])),
                'Workload_Intensity': int(np.mean([log.workload_intensity or 5 for log in all_logs])),
                'Overtime_Hours_Today': np.mean([log.overtime_hours_today or 0.0 for log in all_logs])
            }

            # Cache result
            self._department_averages_cache[department_id] = averages
            print(f"✅ Calculated department {department_id} averages (cached)")
            return averages

        except Exception as e:
            print(f"⚠️ Error calculating department averages: {e}")
            return self.DEFAULT_VALUES.copy()

    def get_global_averages(self) -> Dict[str, float]:
        """
        Get global average feature values across all employees.
        Result is cached for performance.

        Returns:
            Dictionary of average feature values
        """
        if self._global_averages_cache:
            print("✅ Using cached global averages")
            return self._global_averages_cache

        if self.daily_log_repo is None:
            return self.DEFAULT_VALUES.copy()

        try:
            # Get all logs using repository (limited to 1000)
            all_logs = self.daily_log_repo.get_all()

            if not all_logs:
                print("⚠️ No logs found for global averages")
                return self.DEFAULT_VALUES.copy()

            # Take last 1000 logs (already sorted by date desc)
            recent_logs = all_logs[:1000]

            # Calculate averages
            averages = {
                'Work_Hours_Per_Day': np.mean([log.hours_worked or 8.0 for log in recent_logs]),
                'Sleep_Hours_Per_Night': np.mean([log.hours_slept or 7.0 for log in recent_logs]),
                'Personal_Time_Hours_Per_Day': np.mean([log.daily_personal_time or 2.0 for log in recent_logs]),
                'Motivation_Level': int(np.mean([log.motivation_level or 5 for log in recent_logs])),
                'Work_Stress_Level': int(np.mean([log.stress_level or 5 for log in recent_logs])),
                'Workload_Intensity': int(np.mean([log.workload_intensity or 5 for log in recent_logs])),
                'Overtime_Hours_Today': np.mean([log.overtime_hours_today or 0.0 for log in recent_logs])
            }

            self._global_averages_cache = averages
            print("✅ Calculated global averages (cached)")
            return averages

        except Exception as e:
            print(f"⚠️ Error calculating global averages: {e}")
            return self.DEFAULT_VALUES.copy()

    def get_employee_department(self, employee_id: int) -> Optional[int]:
        """
        Get department ID for employee using repository.

        Args:
            employee_id: Employee ID

        Returns:
            Department ID or None
        """
        if self.employee_repo is None:
            print("⚠️ No employee repository available")
            return None

        try:
            # Use repository method instead of direct query
            employee = self.employee_repo.get_by_id(employee_id)

            if employee:
                return employee.department_id
            else:
                print(f"⚠️ Employee {employee_id} not found")
                return None

        except Exception as e:
            print(f"⚠️ Error getting employee department: {e}")
            return None