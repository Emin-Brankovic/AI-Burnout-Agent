"""
Prediction preparation utilities for burnout prediction.
Handles data preparation, synthetic history, and quality assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from backend.domain.entities.daily_log import DailyLogEntity


class PredictionHelper:
    """Handles prediction data preparation and quality assessment."""

    def __init__(self, data_retriever, feature_engineer):
        """
        Initialize prediction helper.

        Args:
            data_retriever: DataRetriever instance
            feature_engineer: FeatureEngineer instance
        """
        self.data_retriever = data_retriever
        self.feature_engineer = feature_engineer

    def create_synthetic_history(
        self,
        entity: DailyLogEntity,
        days_needed: int,
        fallback_values: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Create synthetic historical data using gradual blending.

        Args:
            entity: Current daily log entity
            days_needed: Number of synthetic days to create
            fallback_values: Fallback values to blend from

        Returns:
            DataFrame with synthetic historical data
        """
        synthetic_data = []

        for i in range(days_needed):
            # Gradual transition: earlier days use more fallback
            blend_ratio = (i + 1) / days_needed

            row = {
                'Employee_ID': entity.employee_id,
                'Work_Hours_Per_Day': (
                    fallback_values['Work_Hours_Per_Day'] * (1 - blend_ratio) +
                    (entity.hours_worked or 8.0) * blend_ratio +
                    np.random.uniform(-0.5, 0.5)
                ),
                'Sleep_Hours_Per_Night': (
                    fallback_values['Sleep_Hours_Per_Night'] * (1 - blend_ratio) +
                    (entity.hours_slept or 7.0) * blend_ratio +
                    np.random.uniform(-0.3, 0.3)
                ),
                'Personal_Time_Hours_Per_Day': (
                    fallback_values['Personal_Time_Hours_Per_Day'] * (1 - blend_ratio) +
                    (entity.daily_personal_time or 2.0) * blend_ratio +
                    np.random.uniform(-0.2, 0.2)
                ),
                'Motivation_Level': int(np.clip(
                    fallback_values['Motivation_Level'] * (1 - blend_ratio) +
                    (entity.motivation_level or 5) * blend_ratio +
                    np.random.randint(-1, 2), 1, 10
                )),
                'Work_Stress_Level': int(np.clip(
                    fallback_values['Work_Stress_Level'] * (1 - blend_ratio) +
                    (entity.stress_level or 5) * blend_ratio +
                    np.random.randint(-1, 2), 1, 10
                )),
                'Workload_Intensity': int(np.clip(
                    fallback_values['Workload_Intensity'] * (1 - blend_ratio) +
                    (entity.workload_intensity or 5) * blend_ratio +
                    np.random.randint(-1, 2), 1, 10
                )),
                'Overtime_Hours_Today': max(0,
                    fallback_values['Overtime_Hours_Today'] * (1 - blend_ratio) +
                    (entity.overtime_hours_today or 0.0) * blend_ratio +
                    np.random.uniform(-0.1, 0.1)
                )
            }
            synthetic_data.append(row)

        return pd.DataFrame(synthetic_data)

    def prepare_prediction_data(
        self,
        entity: DailyLogEntity,
        all_features: list
    ) -> Tuple[pd.DataFrame, str, float]:
        """
        Prepare entity for prediction with intelligent fallback.

        Args:
            entity: DailyLogEntity to predict
            all_features: List of all feature names

        Returns:
            Tuple of (prepared DataFrame, data_quality, confidence)
        """
        sequence_length = self.feature_engineer.sequence_length

        # Get historical logs
        historical = self.data_retriever.get_historical_logs(
            employee_id=entity.employee_id,
            limit=sequence_length - 1
        )

        historical_count = len(historical)

        # Current entity as DataFrame
        current_row = pd.DataFrame([{
            'Employee_ID': entity.employee_id,
            'Work_Hours_Per_Day': entity.hours_worked or 8.0,
            'Sleep_Hours_Per_Night': entity.hours_slept or 7.0,
            'Personal_Time_Hours_Per_Day': entity.daily_personal_time or 2.0,
            'Motivation_Level': entity.motivation_level or 5,
            'Work_Stress_Level': entity.stress_level or 5,
            'Workload_Intensity': entity.workload_intensity or 5,
            'Overtime_Hours_Today': entity.overtime_hours_today or 0.0
        }])

        # STRATEGY 1: Sufficient historical data
        if historical_count >= sequence_length - 1:
            df = pd.concat([historical, current_row], ignore_index=True)
            data_quality = "excellent"
            confidence = 0.95
            print(f"✅ Using {historical_count} days of real data")

        # STRATEGY 2: Partial historical data
        elif historical_count > 0:
            days_needed = (sequence_length - 1) - historical_count
            department_id = self.data_retriever.get_employee_department(entity.employee_id)

            if department_id:
                fallback_values = self.data_retriever.get_department_averages(department_id)
                data_quality = "good"
                confidence = 0.80
                print(f"ℹ️ Using {historical_count} real + {days_needed} synthetic (dept avg)")
            else:
                fallback_values = self.data_retriever.get_global_averages()
                data_quality = "fair"
                confidence = 0.65
                print(f"ℹ️ Using {historical_count} real + {days_needed} synthetic (global avg)")

            synthetic = self.create_synthetic_history(entity, days_needed, fallback_values)
            df = pd.concat([synthetic, historical, current_row], ignore_index=True)

        # STRATEGY 3: No historical data
        else:
            days_needed = sequence_length - 1
            department_id = self.data_retriever.get_employee_department(entity.employee_id)

            if department_id:
                fallback_values = self.data_retriever.get_department_averages(department_id)
                data_quality = "estimated_dept"
                confidence = 0.50
                print(f"⚠️ New employee - using dept averages")
            else:
                fallback_values = self.data_retriever.get_global_averages()
                data_quality = "estimated_global"
                confidence = 0.40
                print(f"⚠️ New employee - using global averages")

            synthetic = self.create_synthetic_history(entity, days_needed, fallback_values)
            df = pd.concat([synthetic, current_row], ignore_index=True)

        # Add rolling features
        df_with_rolling, _ = self.feature_engineer.add_rolling_features(df)

        # Get last N days
        last_n_days = df_with_rolling[all_features].tail(sequence_length)

        return last_n_days, data_quality, confidence

    @staticmethod
    def get_risk_level_and_message(
        burnout_rate: float,
        data_quality: str
    ) -> Tuple[str, str]:
        """
        Determine risk level and message based on burnout rate and data quality.

        Args:
            burnout_rate: Predicted burnout rate (0.0 to 1.0)
            data_quality: Data quality indicator

        Returns:
            Tuple of (risk_level, message)
        """
        quality_suffixes = {
            "excellent": "",
            "good": " (based on partial history)",
            "fair": " (limited historical data)",
            "estimated_dept": " (estimated from department data)",
            "estimated_global": " (estimated from company averages)"
        }

        suffix = quality_suffixes.get(data_quality, "")

        if burnout_rate > 0.85:
            return 'CRITICAL', f'URGENT: High burnout rate ({burnout_rate:.1%}) detected{suffix}.'
        elif burnout_rate > 0.70:
            return 'HIGH', f'Warning: {burnout_rate:.1%} burnout rate{suffix}.'
        elif burnout_rate > 0.45:
            return 'MEDIUM', f'Some warning signs detected{suffix}.'
        else:
            return 'NORMAL', f'Healthy balance maintained{suffix}.'