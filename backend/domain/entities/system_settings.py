"""System Settings domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SystemSettingsEntity:
    """System settings domain entity."""
    new_samples_count: int = 0
    retrain_threshold: int = 500
    auto_retrain_enabled: bool = True
    last_retrain_at: Optional[datetime] = None
    retrain_count: int = 0
    id: int = 1  # Singleton ID, usually 1

    def increment_new_samples(self, count: int = 1) -> None:
        """Increment new samples counter."""
        self.new_samples_count += count

    def reset_after_retrain(self) -> None:
        """Reset counters after successful retrain."""
        self.new_samples_count = 0
        self.last_retrain_at = datetime.utcnow()
        self.retrain_count += 1

    def should_retrain(self) -> bool:
        """Check if retraining should be considered."""
        if not self.auto_retrain_enabled:
            return False
        return self.new_samples_count >= self.retrain_threshold
