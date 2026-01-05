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

    def _calculate_feature_completeness(self, entity: DailyLogEntity) -> float:
        """
        Calculate feature completeness score (0.0 to 1.0).
        
        Args:
            entity: DailyLogEntity to evaluate
            
        Returns:
            Completeness score where 1.0 = all features present
        """
        features = {
            'hours_worked': entity.hours_worked,
            'hours_slept': entity.hours_slept,
            'daily_personal_time': entity.daily_personal_time,
            'motivation_level': entity.motivation_level,
            'stress_level': entity.stress_level,
            'workload_intensity': entity.workload_intensity,
            'overtime_hours_today': entity.overtime_hours_today
        }
        
        present_count = sum(1 for value in features.values() if value is not None)
        total_count = len(features)
        
        return present_count / total_count if total_count > 0 else 0.0

    def _calculate_historical_consistency(self, historical: pd.DataFrame) -> float:
        """
        Calculate historical data consistency score (0.0 to 1.0).
        Lower variance = higher consistency = higher confidence.
        
        Args:
            historical: DataFrame with historical data
            
        Returns:
            Consistency score where 1.0 = very consistent
        """
        if historical.empty or len(historical) < 2:
            return 0.5  # Neutral score for insufficient data
        
        # Calculate coefficient of variation for key metrics
        key_metrics = ['Work_Hours_Per_Day', 'Sleep_Hours_Per_Night', 
                      'Work_Stress_Level', 'Motivation_Level']
        
        available_metrics = [m for m in key_metrics if m in historical.columns]
        if not available_metrics:
            return 0.5
        
        cv_scores = []
        for metric in available_metrics:
            values = historical[metric].dropna()
            if len(values) > 1:
                mean_val = values.mean()
                std_val = values.std()
                if mean_val != 0:
                    cv = std_val / mean_val
                    # Convert CV to consistency score (lower CV = higher consistency)
                    # CV of 0 = perfect consistency (1.0), CV of 0.5+ = low consistency (0.0)
                    consistency = max(0.0, 1.0 - (cv * 2))
                    cv_scores.append(consistency)
        
        if not cv_scores:
            return 0.5
        
        # Average consistency across all metrics
        return sum(cv_scores) / len(cv_scores)

    def _calculate_data_quality_confidence(self, historical_count: int, 
                                          sequence_length: int,
                                          has_department: bool) -> Tuple[str, float]:
        """
        Calculate base confidence based on data quality.
        
        Returns:
            Tuple of (data_quality_label, confidence_score)
        """
        if historical_count >= sequence_length - 1:
            return "excellent", 0.95
        elif historical_count > sequence_length // 2:
            return "good", 0.80 if has_department else 0.70
        elif historical_count > 0:
            return "fair", 0.65 if has_department else 0.55
        else:
            return "estimated_dept" if has_department else "estimated_global", 0.50 if has_department else 0.40

    def prepare_prediction_data(
        self,
        entity: DailyLogEntity,
        all_features: list
    ) -> Tuple[pd.DataFrame, str, float]:
        """
        Prepare entity for prediction with intelligent fallback.
        Enhanced confidence calculation considers multiple factors.

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
        department_id = self.data_retriever.get_employee_department(entity.employee_id)
        has_department = department_id is not None

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

        # Calculate base confidence from data quality
        data_quality, base_confidence = self._calculate_data_quality_confidence(
            historical_count, sequence_length, has_department
        )

        # STRATEGY 1: Sufficient historical data
        if historical_count >= sequence_length - 1:
            df = pd.concat([historical, current_row], ignore_index=True)
            print(f"✅ Using {historical_count} days of real data")

        # STRATEGY 2: Partial historical data
        elif historical_count > 0:
            days_needed = (sequence_length - 1) - historical_count

            if department_id:
                fallback_values = self.data_retriever.get_department_averages(department_id)
                print(f"ℹ️ Using {historical_count} real + {days_needed} synthetic (dept avg)")
            else:
                fallback_values = self.data_retriever.get_global_averages()
                print(f"ℹ️ Using {historical_count} real + {days_needed} synthetic (global avg)")

            synthetic = self.create_synthetic_history(entity, days_needed, fallback_values)
            df = pd.concat([synthetic, historical, current_row], ignore_index=True)

        # STRATEGY 3: No historical data
        else:
            days_needed = sequence_length - 1

            if department_id:
                fallback_values = self.data_retriever.get_department_averages(department_id)
                print(f"⚠️ New employee - using dept averages")
            else:
                fallback_values = self.data_retriever.get_global_averages()
                print(f"⚠️ New employee - using global averages")

            synthetic = self.create_synthetic_history(entity, days_needed, fallback_values)
            df = pd.concat([synthetic, current_row], ignore_index=True)

        # Add rolling features
        df_with_rolling, _ = self.feature_engineer.add_rolling_features(df)

        # Get last N days
        last_n_days = df_with_rolling[all_features].tail(sequence_length)

        # Calculate enhanced confidence considering multiple factors
        confidence = self._calculate_enhanced_confidence(
            base_confidence=base_confidence,
            entity=entity,
            historical=historical,
            historical_count=historical_count
        )

        return last_n_days, data_quality, confidence

    def _calculate_enhanced_confidence(
        self,
        base_confidence: float,
        entity: DailyLogEntity,
        historical: pd.DataFrame,
        historical_count: int
    ) -> float:
        """
        Calculate enhanced confidence score considering multiple factors.
        
        Factors considered:
        1. Base data quality confidence
        2. Feature completeness (how many features are present)
        3. Historical data consistency (variance in historical patterns)
        
        Args:
            base_confidence: Base confidence from data quality (0.0 to 1.0)
            entity: Current daily log entity
            historical: Historical data DataFrame
            historical_count: Number of historical records
            
        Returns:
            Enhanced confidence score (0.0 to 1.0)
        """
        # Factor 1: Feature completeness (weight: 20%)
        feature_completeness = self._calculate_feature_completeness(entity)
        completeness_contribution = feature_completeness * 0.20
        
        # Factor 2: Historical consistency (weight: 15%)
        # Only apply if we have sufficient historical data
        if historical_count >= 3:
            consistency = self._calculate_historical_consistency(historical)
            consistency_contribution = consistency * 0.15
        else:
            # Penalize for insufficient historical data
            consistency_contribution = (historical_count / 3.0) * 0.15
        
        # Factor 3: Base data quality (weight: 65%)
        base_contribution = base_confidence * 0.65
        
        # Combine all factors
        enhanced_confidence = (
            base_contribution +
            completeness_contribution +
            consistency_contribution
        )
        
        # Ensure confidence is in valid range [0.0, 1.0]
        enhanced_confidence = max(0.0, min(1.0, enhanced_confidence))
        
        return round(enhanced_confidence, 3)

    @staticmethod
    def get_prediction_type_and_message(
        burnout_rate: float,
        data_quality: str
    ) -> Tuple[str, str]:
        """
        Determine prediction type and message based on burnout rate and data quality.

        Args:
            burnout_rate: Predicted burnout rate (0.0 to 1.0)
            data_quality: Data quality indicator

        Returns:
            Tuple of (prediction_type, message)
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