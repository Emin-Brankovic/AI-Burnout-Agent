from datetime import datetime
from typing import Optional, Tuple
from backend.domain.repositories_interfaces.system_settings_repository_interface import ISystemSettingsRepository
from backend.domain.enums.enums import TrainingDecision

class LearningAgentRunner:
    """
    Implements the Sense -> Think lifecycle for the Self-Learning Agent.
    Strictly handles decision policy. No ML or Web logic.
    """
    
    # Constants for decision logic
    FULL_RETRAINING_THRESHOLD = 500  # >= 500
    INCREMENTAL_RETRAINING_THRESHOLD = 50  # >= 50 (arbitrary minimum for incremental, or just > 0?)
    # NOTE: Prompt says "INCREMENTAL (<500)" implying anything less than 500 but still valid for training.
    # We will assume if it's not SKIP (implicit min threshold usually applies, but prompt didn't specify min).
    # Since "evaluate whether retraining is needed based on ... sample threshold reached", 
    # and default retrain_threshold in entity is now 500, we might need to be careful.
    # However, to support "INCREMENTAL < 500", the runner must trigger below 500.
    # Therefore, we treat strict 500 as the dividing line between FULL and INCREMENTAL.
    # The actual "Trigger" to run AT ALL might be lower, e.g. 50.
    
    def __init__(self, settings_repository: ISystemSettingsRepository):
        self._settings_repo = settings_repository

    def run_cycle(self) -> Tuple[TrainingDecision, dict]:
        """
        Execute one Sense -> Think cycle.
        
        Returns:
            Tuple[TrainingDecision, dict]: The decision and context metadata.
        """
        # 1. Sense: Read System State
        settings = self._settings_repo.get_settings()
        
        # 2. Think: Evaluate Deterministic Rules
        decision = TrainingDecision.SKIP
        reason = "No action required"
        
        if not settings.auto_retrain_enabled:
            return TrainingDecision.SKIP, {
                "reason": "Auto-retrain disabled",
                "current_samples": settings.new_samples_count
            }

        # Logic: 
        # If user demands "sample threshold reached" (Entity defaults to 500), 
        # strictly speaking we only trigger at 500. 
        # BUT the prompt asks for "INCREMENTAL (<500)". 
        # The only way to get INCREMENTAL is if we ignore the entity's .should_retrain() 
        # (which checks >= threshold) OR if we interpret "threshold" differently.
        # Implemented Strategy: 
        # - Triggers if >= 50 (Minimum useful batch). 
        # - < 500 -> Incremental
        # - >= 500 -> Full
        
        # We verify against a hard minimum to avoid micro-training on 1 sample.
        MIN_SAMPLES_TO_TRAIN = 50 
        
        # Check against the User Configured Threshold (500) for FULL
        # Check against MIN for INCREMENTAL
        
        if settings.new_samples_count >= self.FULL_RETRAINING_THRESHOLD:
            decision = TrainingDecision.FULL_RETRAINING
            reason = f"Full threshold reached ({settings.new_samples_count} >= {self.FULL_RETRAINING_THRESHOLD})"
            
        elif settings.new_samples_count >= MIN_SAMPLES_TO_TRAIN:
            # Check if we should wait for full? 
            # Prompt implies we DO incremental if < 500.
            decision = TrainingDecision.INCREMENTAL_TRAINING
            reason = f"Incremental batch ready ({settings.new_samples_count} samples)"
        else:
            decision = TrainingDecision.SKIP
            reason = f"Insufficient samples ({settings.new_samples_count} < {MIN_SAMPLES_TO_TRAIN})"

        return decision, {
            "reason": reason,
            "new_samples_count": settings.new_samples_count,
            "threshold_full": self.FULL_RETRAINING_THRESHOLD,
            "threshold_min": MIN_SAMPLES_TO_TRAIN,
            "timestamp": datetime.utcnow().isoformat()
        }
