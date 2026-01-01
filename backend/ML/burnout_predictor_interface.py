"""
Abstract Base Class for ML Burnout Predictor.

Defines contract for burnout prediction models using ABC,
ensuring all implementations provide required methods.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from backend.domain.entities.daily_log import DailyLogEntity

@dataclass
class TrainingSample:
    """
    Single training sample for burnout prediction.

    Attributes:
        employee_id: Employee identifier
        burnout_rate: Target burnout rate (0.0 to 1.0)
    """

    employee_id: int
    work_hours_per_day: float
    sleep_hours_per_night: float
    personal_time_hours_per_day: float
    motivation_level: int
    work_stress_level: int
    workload_intensity: int
    overtime_hours_today: float
    burnout_rate:float


@dataclass
class EvaluationMetrics:
    """
    Model evaluation metrics.

    Attributes:
        train_r2_score: R² score on training set
        test_r2_score: R² score on test set
        train_samples: Number of training samples
        test_samples: Number of test samples
        features_count: Number of features used
        mse: Mean Squared Error (optional)
        mae: Mean Absolute Error (optional)
    """
    train_r2_score: float
    test_r2_score: float
    train_samples: int
    test_samples: int
    features_count: int
    mse: Optional[float] = None
    mae: Optional[float] = None


@dataclass
class PredictionResult:
    """
    Burnout prediction result.

    Attributes:
        burnout_rate: Predicted burnout rate (0.0 to 1.0)
        risk_level: Risk level (NORMAL, LOW, MEDIUM, HIGH, CRITICAL)
        message: Human-readable explanation
        confidence: Model confidence (optional)
    """
    burnout_rate: float
    risk_level: str
    message: str
    confidence: Optional[float] = None


class IBurnoutPredictor(ABC):
    """
    Abstract base class for ML burnout predictor.

    All concrete implementations must implement these abstract methods.
    Different implementations could be:
    - RidgeRegressionPredictor (current)
    - RandomForestPredictor
    - GradientBoostingPredictor
    - NeuralNetworkPredictor
    """

    @abstractmethod
    async def train(
            self,
            training_data: List[TrainingSample],
            model_path: str,
            test_size: float = 0.2
    ) -> EvaluationMetrics:
        """
        Train model on given data.

        Args:
            training_data: List of training samples with features and targets
            model_path: Path where model will be saved
            test_size: Fraction of data to use for testing (default: 0.2)

        Returns:
            EvaluationMetrics: Training and validation metrics

        Raises:
            ValueError: If insufficient training data
        """
        pass

    # @abstractmethod
    # def train_from_csv(
    #         self,
    #         csv_path: str,
    #         model_path: str,
    #         test_size: float = 0.2
    # ) -> EvaluationMetrics:
    #     """
    #     Train model directly from CSV file.
    #
    #     Args:
    #         csv_path: Path to CSV file with historical data
    #         model_path: Path where model will be saved
    #         test_size: Fraction of data to use for testing
    #
    #     Returns:
    #         EvaluationMetrics: Training and validation metrics
    #     """
    #     pass

    @abstractmethod
    def evaluate(
            self,
            validation_data: List[TrainingSample]
    ) -> EvaluationMetrics:
        """
        Evaluate model on validation data.

        Args:
            validation_data: List of samples for validation

        Returns:
            EvaluationMetrics: Evaluation metrics

        Raises:
            RuntimeError: If model not loaded
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """
        Load model from disk.

        Args:
            model_path: Path to model file

        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        pass

    @abstractmethod
    def predict(self, entity: DailyLogEntity) -> PredictionResult:
        """
        Predict burnout rate for a single employee log.

        Args:
            entity: DailyLogEntity with employee metrics

        Returns:
            PredictionResult: Prediction with risk level and message

        Raises:
            RuntimeError: If model not loaded
            ValueError: If entity has invalid data
        """
        pass

    # @abstractmethod
    # def predict_raw(self, features: Dict[str, Any]) -> float:
    #     """
    #     Predict raw burnout rate from feature dictionary.
    #
    #     Args:
    #         features: Dictionary of feature values
    #
    #     Returns:
    #         Raw burnout rate (0.0 to 1.0)
    #     """
    #     pass

    @abstractmethod
    def predict_batch(
            self,
            entities: List[DailyLogEntity]
    ) -> List[PredictionResult]:
        """
        Predict for batch of employee logs.

        Args:
            entities: List of DailyLogEntity instances

        Returns:
            List of PredictionResult instances
        """
        pass

    @abstractmethod
    def save_prediction_to_data(
            self,
            employee_id: int,
            features: Dict[str, Any],
            predicted_burnout: float
    ) -> None:
        """
        Save prediction back to training data CSV.

        Args:
            employee_id: Employee ID
            features: Feature dictionary
            predicted_burnout: Predicted burnout rate
        """
        pass

    @property
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """
        Check if model is loaded and ready.

        Returns:
            True if model is loaded, False otherwise
        """
        pass


    # @property
    # @abstractmethod
    # def model_metadata(self) -> Dict[str, Any]:
    #     """
    #     Get model metadata (algorithm, version, training date, etc.).
    #
    #     Returns:
    #         Dictionary with model metadata
    #     """
    #     pass
