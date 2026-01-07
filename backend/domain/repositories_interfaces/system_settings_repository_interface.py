from abc import ABC, abstractmethod
from backend.domain.entities.system_settings import SystemSettingsEntity

class ISystemSettingsRepository(ABC):
    @abstractmethod
    def get_settings(self) -> SystemSettingsEntity:
        """Get the singleton system settings. Create if not exists."""
        pass

    @abstractmethod
    def update_settings(self, settings: SystemSettingsEntity) -> SystemSettingsEntity:
        """Update system settings."""
        pass
    
    @abstractmethod
    def increment_samples(self, count: int = 1) -> SystemSettingsEntity:
        """Atomically increment samples count."""
        pass
    
    @abstractmethod
    def record_retrain_success(self) -> SystemSettingsEntity:
        """Atomically update state after successful retrain."""
        pass
