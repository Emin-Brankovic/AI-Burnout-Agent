import threading
import logging
from typing import Optional, List
from backend.ML.burnout_predictor_interface import IBurnoutPredictor, PredictionResult
from backend.domain.entities.daily_log import DailyLogEntity

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Singleton-like service to hold the currently active ML model.
    Supports atomic hot-swapping.
    """
    _instance = None
    _lock = threading.RLock()
    _current_model: Optional[IBurnoutPredictor] = None  # Share state across instances if we rely on class var, OR use __new__
    
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
        # self._current_model is already handled if we assume dynamic state, 
        # but let's initialize it safely.
        # However, _current_model as instance var is better.

    def load_new_model(self, predictor: IBurnoutPredictor):
        """
        Hot-swap the current model with a new loaded predictor.
        Thread-safe.
        """
        if not predictor.is_model_loaded:
            raise ValueError("Predictor must have model loaded before swapping")
            
        with self._lock:
            # Atomic reference switch
            old_model = self._current_model
            self._current_model = predictor
            logger.info("🔥 Model successfully hot-swapped.")
            
            # Explicitly clear old model if needed, though GC handles it usually.
            # In complex scenarios (e.g. TensorFlow sessions), explicit close() needed.
            del old_model

    @property
    def active_model(self) -> Optional[IBurnoutPredictor]:
        """Get the currently active predictor."""
        with self._lock:
            return self._current_model
            
    def predict(self, entity: DailyLogEntity) -> PredictionResult:
        """
        Proxy method to predict using active model.
        """
        # Snapshot reference to avoid race condition if swapped mid-execution
        model = self.active_model
        
        if not model or not model.is_model_loaded:
            raise RuntimeError("No active model loaded in registry")
            
        return model.predict(entity)
