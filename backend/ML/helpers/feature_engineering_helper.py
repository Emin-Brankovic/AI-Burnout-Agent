"""
Feature Engineering utilities for burnout prediction.
Handles rolling averages and sliding window creation.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


class FeatureEngineer:
    """Handles feature transformation and engineering for burnout prediction."""

    def __init__(self, sequence_length: int = 7, rolling_window: int = 7):
        """
        Initialize feature engineer.

        Args:
            sequence_length: Number of days in sliding window
            rolling_window: Window size for rolling averages
        """
        self.sequence_length = sequence_length
        self.rolling_window = rolling_window

        self.base_features = [
            'Work_Hours_Per_Day',
            'Sleep_Hours_Per_Night',
            'Personal_Time_Hours_Per_Day',
            'Motivation_Level',
            'Work_Stress_Level',
            'Workload_Intensity',
            'Overtime_Hours_Today'
        ]

        self.rolling_feature_names = [
            'Work_Hours_Per_Day',
            'Work_Stress_Level',
            'Motivation_Level'
        ]

    def add_rolling_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Add rolling average features to DataFrame.

        Args:
            df: DataFrame with employee data

        Returns:
            Tuple of (DataFrame with rolling features, list of all feature names)
        """
        df = df.sort_values('Employee_ID').copy()
        rolling_features = []

        for feature in self.rolling_feature_names:
            rolling_col = f'{feature}_rolling_{self.rolling_window}d'
            df[rolling_col] = df.groupby('Employee_ID')[feature].transform(
                lambda x: x.rolling(window=self.rolling_window, min_periods=1).mean()
            )
            rolling_features.append(rolling_col)

        all_features = self.base_features + rolling_features
        return df, all_features

    def create_sliding_window_features(
        self,
        df: pd.DataFrame,
        feature_list: List[str],
        target_col: str = 'Burnout_Rate_Daily'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sliding window features for time series prediction.

        Args:
            df: DataFrame with features
            feature_list: List of feature column names
            target_col: Target column name

        Returns:
            Tuple of (X array, y array)
        """
        X_list = []
        y_list = []

        for employee_id, group in df.groupby('Employee_ID'):
            if len(group) <= self.sequence_length:
                continue

            data_values = group[feature_list].values
            target_values = group[target_col].values

            for i in range(len(data_values) - self.sequence_length):
                window = data_values[i: i + self.sequence_length].flatten()
                X_list.append(window)
                y_list.append(target_values[i + self.sequence_length])

        return np.array(X_list), np.array(y_list)