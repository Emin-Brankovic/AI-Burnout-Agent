import threading
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable, Tuple

from backend.ML.burnout_predictor_interface import IBurnoutPredictor, PredictionResult
from backend.domain.entities.daily_log import DailyLogEntity

logger = logging.getLogger(__name__)

# Version format constants
VERSION_PREFIX = "BurnoutAgentModel v"
VERSION_PATTERN = re.compile(r"BurnoutAgentModel v(\d+)")


class ModelRegistry:
    """
    Singleton-like service to hold the currently active ML model.
    Supports atomic hot-swapping with automatic version detection.
    
    Key Features:
    - Thread-safe model swapping
    - Automatic detection of new model versions via file timestamps
    - Model version tracking for prediction outputs (format: BurnoutAgentModel vX)
    - Integration with database version records
    """
    _instance = None
    _lock = threading.RLock()
    _current_model: Optional[IBurnoutPredictor] = None
    _current_version: Optional[str] = None  # Version string (e.g., "BurnoutAgentModel v1")
    _current_version_number: int = 0  # Numeric version for incrementing
    _model_file_mtime: Optional[float] = None  # Last modification time of model file
    _model_path: Optional[str] = None  # Path to the currently loaded model file
    
    # Default model path
    DEFAULT_MODEL_PATH = 'backend/ml_models/burnout_model.pkl'
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        # Initialize version tracking
        self._model_factory: Optional[Callable[[], IBurnoutPredictor]] = None
        self._auto_reload_enabled = True
        self._last_version_check: Optional[datetime] = None
        self._version_check_interval_seconds = 5  # Check every 5 seconds minimum

    def set_model_factory(self, factory: Callable[[], IBurnoutPredictor]):
        """
        Set the factory function for creating new predictor instances.
        Required for automatic hot-swapping.
        
        Args:
            factory: Function that returns a new IBurnoutPredictor instance
        """
        with self._lock:
            self._model_factory = factory
            logger.info("🏭 Model factory configured for hot-swapping")

    def load_new_model(
        self, 
        predictor: IBurnoutPredictor, 
        version: Optional[str] = None,
        model_path: Optional[str] = None
    ):
        """
        Hot-swap the current model with a new loaded predictor.
        Thread-safe with version tracking.
        
        Args:
            predictor: The loaded predictor instance
            version: Optional version string (auto-generated if not provided)
            model_path: Path to the model file (for timestamp tracking)
        """
        if not predictor.is_model_loaded:
            raise ValueError("Predictor must have model loaded before swapping")
        
        # Determine model path for tracking
        effective_path = model_path or self.DEFAULT_MODEL_PATH
        
        # Auto-generate version if not provided
        if version is None:
            version = self._generate_version_from_file(effective_path)
            
        with self._lock:
            old_version = self._current_version
            old_model = self._current_model
            
            # Atomic reference switch
            self._current_model = predictor
            self._current_version = version
            self._current_version_number = self._extract_version_number(version)
            self._model_path = effective_path
            
            # Update file modification time for tracking
            if Path(effective_path).exists():
                self._model_file_mtime = os.path.getmtime(effective_path)
            
            logger.info(f"🔥 Model hot-swapped: {old_version} → {version}")
            
            # Cleanup old model reference
            del old_model

    def _generate_version_from_file(self, model_path: str) -> str:
        """
        Generate next version string by incrementing current version number.
        Format: BurnoutAgentModel vX (e.g., BurnoutAgentModel v1, v2, etc.)
        
        Args:
            model_path: Path to the model file (used for fallback)
            
        Returns:
            Version string in format 'BurnoutAgentModel vX'
        """
        # Try to get latest version from database
        next_version = self._get_next_version_number()
        return f"{VERSION_PREFIX}{next_version}"
    
    def _get_next_version_number(self) -> int:
        """
        Get the next version number by checking database and current state.
        
        Returns:
            Next version number (1 if first model, otherwise latest + 1)
        """
        # Start with current known version
        max_version = self._current_version_number
        
        # Try to query database for latest version
        try:
            from backend.infrastructure.persistence.database import SessionLocal
            from backend.infrastructure.persistence.repositories.model_version_repository import ModelVersionRepository
            
            db = SessionLocal()
            try:
                version_repo = ModelVersionRepository(db)
                latest = version_repo.get_latest()
                if latest and latest.version_number:
                    # Extract version number from string
                    match = VERSION_PATTERN.match(latest.version_number)
                    if match:
                        db_version = int(match.group(1))
                        max_version = max(max_version, db_version)
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not query DB for latest version: {e}")
        
        return max_version + 1
    
    def _extract_version_number(self, version_string: str) -> int:
        """
        Extract numeric version from version string.
        
        Args:
            version_string: Version string like 'BurnoutAgentModel v3'
            
        Returns:
            Version number (e.g., 3) or 0 if not parseable
        """
        if not version_string:
            return 0
        match = VERSION_PATTERN.match(version_string)
        if match:
            return int(match.group(1))
        return 0

    def check_and_reload_if_needed(self) -> bool:
        """
        Check if model file has been updated and reload if necessary.
        Thread-safe, rate-limited to avoid excessive file system checks.
        
        Returns:
            True if model was reloaded, False otherwise
        """
        if not self._auto_reload_enabled or not self._model_factory:
            return False
            
        # Rate limit version checks
        now = datetime.utcnow()
        if self._last_version_check:
            elapsed = (now - self._last_version_check).total_seconds()
            if elapsed < self._version_check_interval_seconds:
                return False
        
        with self._lock:
            self._last_version_check = now
            
            # Check file modification time
            model_path = self._model_path or self.DEFAULT_MODEL_PATH
            if not Path(model_path).exists():
                return False
                
            current_mtime = os.path.getmtime(model_path)
            
            # If file has been modified since last load
            if self._model_file_mtime is None or current_mtime > self._model_file_mtime:
                logger.info(f"🔄 New model version detected at {model_path}")
                
                try:
                    # Create new predictor instance
                    new_predictor = self._model_factory()
                    new_predictor.load_model(model_path)
                    
                    # Generate new version
                    new_version = self._generate_version_from_file(model_path)
                    
                    # Swap (we're already holding the lock)
                    old_version = self._current_version
                    old_model = self._current_model
                    
                    self._current_model = new_predictor
                    self._current_version = new_version
                    self._current_version_number = self._extract_version_number(new_version)
                    self._model_file_mtime = current_mtime
                    
                    logger.info(f"✅ Auto-reloaded model: {old_version} → {new_version}")
                    
                    del old_model
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Failed to auto-reload model: {e}")
                    return False
                    
        return False

    @property
    def active_model(self) -> Optional[IBurnoutPredictor]:
        """Get the currently active predictor."""
        with self._lock:
            return self._current_model
    
    @property
    def current_version(self) -> Optional[str]:
        """Get the current model version string."""
        with self._lock:
            return self._current_version
    
    @property
    def model_info(self) -> dict:
        """
        Get comprehensive model information.
        
        Returns:
            Dictionary with version, path, loaded_at, etc.
        """
        with self._lock:
            return {
                "version": self._current_version,
                "model_path": self._model_path,
                "file_mtime": datetime.fromtimestamp(self._model_file_mtime).isoformat() 
                             if self._model_file_mtime else None,
                "is_loaded": self._current_model is not None and self._current_model.is_model_loaded,
                "auto_reload_enabled": self._auto_reload_enabled
            }
            
    def predict(self, entity: DailyLogEntity) -> Tuple[PredictionResult, str]:
        """
        Proxy method to predict using active model.
        Returns prediction result along with model version used.
        
        Args:
            entity: DailyLogEntity to predict
            
        Returns:
            Tuple of (PredictionResult, model_version)
        """
        # Check for new model before prediction (rate-limited)
        self.check_and_reload_if_needed()
        
        # Snapshot reference to avoid race condition if swapped mid-execution
        with self._lock:
            model = self._current_model
            version = self._current_version or "unknown"
        
        if not model or not model.is_model_loaded:
            raise RuntimeError("No active model loaded in registry")
        
        result = model.predict(entity)
        return result, version
    
    def enable_auto_reload(self, enabled: bool = True):
        """Enable or disable automatic model reloading."""
        with self._lock:
            self._auto_reload_enabled = enabled
            logger.info(f"🔄 Auto-reload {'enabled' if enabled else 'disabled'}")
