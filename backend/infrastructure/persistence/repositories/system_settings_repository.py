from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import update
from backend.domain.repositories_interfaces.system_settings_repository_interface import ISystemSettingsRepository
from backend.domain.entities.system_settings import SystemSettingsEntity
from backend.infrastructure.persistence.database import SystemSettings
from backend.infrastructure.persistence.data_mappers import (
    system_settings_model_to_entity,
    system_settings_entity_to_model
)

class SystemSettingsRepository(ISystemSettingsRepository):
    """SQLAlchemy implementation of SystemSettingsRepository."""

    def __init__(self, session: Session):
        self.session = session
        self.SYSTEM_ID = 1

    def _ensure_settings_exists(self) -> SystemSettings:
        """Internal helper to ensure record exists."""
        settings = self.session.query(SystemSettings).filter(
            SystemSettings.id == self.SYSTEM_ID
        ).first()

        if not settings:
            settings = SystemSettings(id=self.SYSTEM_ID)
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        
        return settings

    def get_settings(self) -> SystemSettingsEntity:
        """Get the singleton system settings. Create if not exists."""
        model = self._ensure_settings_exists()
        return system_settings_model_to_entity(model)

    def update_settings(self, settings: SystemSettingsEntity) -> SystemSettingsEntity:
        """Update system settings."""
        try:
            model = self.session.query(SystemSettings).filter(
                SystemSettings.id == self.SYSTEM_ID
            ).first()

            if not model:
                model = system_settings_entity_to_model(settings)
                model.id = self.SYSTEM_ID
                self.session.add(model)
            else:
                model.new_samples_count = settings.new_samples_count
                model.retrain_threshold = settings.retrain_threshold
                model.auto_retrain_enabled = settings.auto_retrain_enabled
                model.last_retrain_at = settings.last_retrain_at
                model.retrain_count = settings.retrain_count

            self.session.commit()
            self.session.refresh(model)
            return system_settings_model_to_entity(model)
        except Exception as e:
            self.session.rollback()
            raise e

    def increment_samples(self, count: int = 1) -> SystemSettingsEntity:
        """Atomically increment samples count."""
        try:
            # Ensure exists first to avoid update on non-existent row
            self._ensure_settings_exists()
            
            # Atomic update using SQLAlchemy expression
            self.session.execute(
                update(SystemSettings)
                .where(SystemSettings.id == self.SYSTEM_ID)
                .values(new_samples_count=SystemSettings.new_samples_count + count)
            )
            self.session.commit()
            return self.get_settings()
        except Exception as e:
            self.session.rollback()
            raise e

    def record_retrain_success(self) -> SystemSettingsEntity:
        """Atomically update state after successful retrain."""
        try:
            self._ensure_settings_exists()
            
            self.session.execute(
                update(SystemSettings)
                .where(SystemSettings.id == self.SYSTEM_ID)
                .values(
                    new_samples_count=0,
                    retrain_count=SystemSettings.retrain_count + 1,
                    last_retrain_at=datetime.utcnow()
                )
            )
            self.session.commit()
            return self.get_settings()
        except Exception as e:
            self.session.rollback()
            raise e
