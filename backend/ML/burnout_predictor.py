"""
Ridge Regression implementation of IBurnoutPredictor.
Refactored to use helper modules for clean separation of concerns.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

from backend.ML.burnout_predictor_interface import (
    IBurnoutPredictor,
    TrainingSample,
    EvaluationMetrics,
    PredictionResult
)
from backend.ML.helpers.feature_engineering_helper import FeatureEngineer
from backend.ML.helpers.data_retrieval_helper import DataRetriever
from backend.ML.helpers.prediction_helper import PredictionHelper
from backend.domain.entities.daily_log import DailyLogEntity
from backend.domain.repositories_interfaces.daily_log_repository_interface import DailyLogRepositoryInterface
from backend.domain.repositories_interfaces.employee_repository_interface import EmployeeRepositoryInterface


class BurnoutPredictor(IBurnoutPredictor):
    """
    Ridge Regression implementation for burnout prediction.
    Uses helper modules for clean separation of concerns.
    """

    def save_prediction_to_data(self, employee_id: int, features: Dict[str, Any], predicted_burnout: float) -> None:
        pass

    # Model paths
    MODEL_PATH = 'backend/ml_models/burnout_model.pkl'
    SCALER_PATH = 'backend/ml_models/scaler.pkl'
    FEATURES_PATH = 'backend/ml_models/burnout_model_features.pkl'

    TARGET = 'Burnout_Rate_Daily'

    def __init__(
            self,
            daily_log_repo: Optional[DailyLogRepositoryInterface] = None,  # ← OPTIONAL
            employee_repo: Optional[EmployeeRepositoryInterface] = None  # ← OPTIONAL
    ):
        """
        Initialize predictor with helper modules.

        Args:
            db_session: Optional database session for querying historical data
        """
        # Core ML components
        self._model: Ridge = None
        self._scaler: MinMaxScaler = None
        self._all_features: List[str] = []

        # Helper modules
        self.feature_engineer = FeatureEngineer(sequence_length=7, rolling_window=7)
        self.data_retriever = DataRetriever(
            daily_log_repository=daily_log_repo,
            employee_repository=employee_repo
        )
        self.prediction_helper = PredictionHelper(
            data_retriever=self.data_retriever,
            feature_engineer=self.feature_engineer
        )

    # def set_db_session(self, db_session: Session):
    #     """Set database session for data retrieval."""
    #     self.data_retriever.set_db_session(db_session)

    # ========== DATA CONVERSION ==========

    def _samples_to_dataframe(self, samples: List[TrainingSample]) -> pd.DataFrame:
        """Convert TrainingSample list to DataFrame."""
        data = []
        for sample in samples:
            row = {
                'Employee_ID': sample.employee_id,
                'Work_Hours_Per_Day': sample.work_hours_per_day,
                'Sleep_Hours_Per_Night': sample.sleep_hours_per_night,
                'Personal_Time_Hours_Per_Day': sample.personal_time_hours_per_day,
                'Motivation_Level': sample.motivation_level,
                'Work_Stress_Level': sample.work_stress_level,
                'Workload_Intensity': sample.workload_intensity,
                'Overtime_Hours_Today': sample.overtime_hours_today,
                'Burnout_Rate_Daily': sample.burnout_rate
            }
            data.append(row)
        return pd.DataFrame(data)

    # ========== TRAINING ==========

    async def train(
        self,
        training_data: List[TrainingSample],
        model_path: str = 'backend/ml_models/burnout_model.pkl',
        test_size: float = 0.2
    ) -> EvaluationMetrics:
        """
        Train Ridge regression model.

        Args:
            training_data: List of training samples
            model_path: Path to save the model
            test_size: Proportion of data for testing

        Returns:
            EvaluationMetrics with training results
        """
        print(f"📚 Training model with {len(training_data)} samples...")

        # Convert to DataFrame
        df = self._samples_to_dataframe(training_data)
        print(f"Initial dataset: {df.shape}")
        print(f"Unique employees: {df['Employee_ID'].nunique()}")

        # Add rolling features
        df, self._all_features = self.feature_engineer.add_rolling_features(df)
        print(f"Total features: {len(self._all_features)}")

        # Scale features
        self._scaler = MinMaxScaler()
        df[self._all_features] = self._scaler.fit_transform(df[self._all_features])

        # Create sliding windows
        X, y = self.feature_engineer.create_sliding_window_features(
            df, self._all_features, self.TARGET
        )

        if len(X) == 0:
            raise ValueError(
                f"No training samples created. Need at least "
                f"{self.feature_engineer.sequence_length + 1} days per employee."
            )

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        print(f"Training samples: {X_train.shape[0]}")
        print(f"Test samples: {X_test.shape[0]}")

        # Train model
        self._model = Ridge(alpha=1.0)
        self._model.fit(X_train, y_train)

        # Calculate metrics
        train_score = self._model.score(X_train, y_train)
        test_score = self._model.score(X_test, y_test)
        y_pred = self._model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        print(f"Train R² Score: {train_score:.4f}")
        print(f"Test R² Score: {test_score:.4f}")

        # Save model
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self._model, self.MODEL_PATH)
        joblib.dump(self._scaler, self.SCALER_PATH)
        joblib.dump(self._all_features, self.FEATURES_PATH)

        print(f"✅ Model saved to '{model_path}'")

        return EvaluationMetrics(
            train_r2_score=train_score,
            test_r2_score=test_score,
            train_samples=len(X_train),
            test_samples=len(X_test),
            features_count=len(self._all_features),
            mse=mse,
            mae=mae
        )

    # ========== EVALUATION ==========

    def evaluate(
        self,
        validation_data: List[TrainingSample],
        test_size: float = 0.2
    ) -> EvaluationMetrics:
        """
        Evaluate model on validation data.

        Args:
            validation_data: List of validation samples
            test_size: Proportion of data for testing

        Returns:
            EvaluationMetrics with evaluation results
        """
        if not self.is_model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Convert to DataFrame
        df = self._samples_to_dataframe(validation_data)
        df, _ = self.feature_engineer.add_rolling_features(df)
        df[self._all_features] = self._scaler.transform(df[self._all_features])

        # Create windows
        X, y = self.feature_engineer.create_sliding_window_features(
            df, self._all_features, self.TARGET
        )

        if len(X) == 0:
            raise ValueError("Not enough validation data")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Evaluate
        score = self._model.score(X_test, y_test)
        y_pred = self._model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        return EvaluationMetrics(
            train_r2_score=0.0,
            test_r2_score=score,
            train_samples=0,
            test_samples=len(X_test),
            features_count=len(self._all_features),
            mse=mse,
            mae=mae
        )

    # ========== MODEL MANAGEMENT ==========

    def load_model(self, model_path: str = None) -> None:
        """
        Load trained model from disk.

        Args:
            model_path: Optional path to model file
        """
        if model_path is None:
            model_path = self.MODEL_PATH

        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self._model = joblib.load(model_path)
        self._scaler = joblib.load(self.SCALER_PATH)
        self._all_features = joblib.load(self.FEATURES_PATH)

        print("✅ Model, scaler, and features loaded successfully")

    @property
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None and self._scaler is not None

    # ========== PREDICTION ==========

    def predict(self, entity: DailyLogEntity) -> PredictionResult:
        """
        Predict burnout for entity using intelligent fallback strategies.

        Args:
            entity: DailyLogEntity to predict

        Returns:
            PredictionResult with burnout rate, risk level, and confidence
        """
        if not self.is_model_loaded:
            self.load_model()

        # Prepare prediction data with fallback strategies
        features_df, data_quality, base_confidence = self.prediction_helper.prepare_prediction_data(
            entity=entity,
            all_features=self._all_features
        )

        # Scale features
        scaled_input = self._scaler.transform(features_df)

        # Flatten to sliding window
        sliding_window = scaled_input.flatten().reshape(1, -1)

        # Predict
        predicted_rate = self._model.predict(sliding_window)[0]
        predicted_rate = max(0.0, min(1.0, predicted_rate))  # Clip to [0, 1]

        # Calculate model prediction uncertainty (based on distance from training distribution)
        # For Ridge regression, we can use the prediction's distance from typical values
        model_uncertainty_penalty = self._calculate_model_uncertainty(
            sliding_window=sliding_window,
            predicted_rate=predicted_rate
        )

        # Adjust confidence based on model uncertainty
        # Higher uncertainty = lower confidence
        final_confidence = base_confidence * (1.0 - model_uncertainty_penalty)
        final_confidence = max(0.0, min(1.0, final_confidence))  # Ensure valid range

        # Determine prediction type
        prediction_type, message = self.prediction_helper.get_prediction_type_and_message(
            burnout_rate=predicted_rate,
            data_quality=data_quality
        )

        return PredictionResult(
            burnout_rate=predicted_rate,
            burnout_risk=prediction_type,
            message=message,
            confidence_score=round(final_confidence, 3)
            #confidence_score=round(final_confidence, 3)  # Round to 3 decimal places
        )

    def _calculate_model_uncertainty(
        self,
        sliding_window: np.ndarray,
        predicted_rate: float
    ) -> float:
        """
        Calculate model prediction uncertainty penalty (0.0 to 0.3).
        
        This estimates how far the prediction is from the model's training distribution.
        Higher penalty = lower confidence.
        
        Args:
            sliding_window: Scaled input features for prediction
            predicted_rate: Predicted burnout rate
            
        Returns:
            Uncertainty penalty (0.0 = no penalty, 0.3 = maximum penalty)
        """
        try:
            # Check if prediction is in extreme ranges (very low or very high)
            # Extreme predictions may be less reliable
            if predicted_rate < 0.1 or predicted_rate > 0.9:
                # Extreme predictions get a small penalty
                return 0.10
            
            # Check feature values for outliers
            # If features are very different from typical values, add penalty
            feature_std = np.std(sliding_window)
            if feature_std > 0.5:  # High variance in features
                return 0.15
            
            # Check for NaN or infinite values
            if np.any(np.isnan(sliding_window)) or np.any(np.isinf(sliding_window)):
                return 0.25
            
            # Default: low uncertainty
            return 0.05
            
        except Exception:
            # If calculation fails, apply moderate penalty
            return 0.10

    def predict_batch(self, entities: List[DailyLogEntity]) -> List[PredictionResult]:
        """
        Predict for multiple entities.

        Args:
            entities: List of DailyLogEntity objects

        Returns:
            List of PredictionResult objects
        """
        return [self.predict(entity) for entity in entities]