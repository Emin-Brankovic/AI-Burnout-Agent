from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.domain.enums.enums import TrainingMode
from backend.domain.entities.system_settings import SystemSettingsEntity

class ITrainer(ABC):
    """
    Abstract interface for Model Trainer.
    Decouples the agent from specific ML frameworks (PyTorch, TensorFlow, Scikit-Learn).
    Hides the underlying implementation details of the training loop.
    """

    @abstractmethod
    def retrain(
        self, 
        mode: TrainingMode, 
        dataset_reference: str, 
        settings: SystemSettingsEntity
    ) -> Dict[str, Any]:
        """
        Execute the model retraining process.

        Args:
            mode (TrainingMode): Type of training (e.g. INCREMENTAL or FULL).
            dataset_reference (str): Reference to the dataset (e.g., file path, URI, or table name).
            settings (SystemSettingsEntity): Configuration and thresholds for the training session.

        Returns:
            Dict[str, Any]: detailed training result metadata, including:
                - success (bool)
                - metrics (dict): e.g. {"accuracy": 0.85, "loss": 0.12}
                - model_version (str)
                - timestamp (isoformat)
        """
        pass
