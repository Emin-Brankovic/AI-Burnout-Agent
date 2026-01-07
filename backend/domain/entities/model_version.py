"""ModelVersion domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ModelVersionEntity:
    """
    ModelVersion domain entity.
    Tracks history of trained models.
    """
    version_number: str
    training_mode: str
    dataset_size: int
    model_file_path: str
    accuracy: Optional[float] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def __post_init__(self):
        if not self.version_number:
            raise ValueError("Version number cannot be empty")
        if not self.model_file_path:
            raise ValueError("Model file path cannot be empty")
        if self.dataset_size < 0:
            raise ValueError("Dataset size cannot be negative")
