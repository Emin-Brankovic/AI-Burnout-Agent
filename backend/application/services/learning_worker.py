import threading
import time
import logging
from typing import Optional
from datetime import datetime

from backend.domain.enums.enums import TrainingDecision
from backend.domain.interfaces.trainer_interface import ITrainer
from backend.application.services.learning_agent_runner import LearningAgentRunner
from backend.application.services.dataset_formatter_service import DatasetFormatterService
from backend.application.services.model_registry import ModelRegistry
from backend.infrastructure.persistence.database import get_db, SessionLocal
from backend.infrastructure.persistence.repositories.system_settings_repository import SystemSettingsRepository
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.model_version_repository import ModelVersionRepository
from backend.domain.entities.model_version import ModelVersionEntity
from backend.ML.burnout_predictor_interface import IBurnoutPredictor

logger = logging.getLogger(__name__)

class LearningWorker:
    """
    Background worker that periodically triggers the Learning Agent Runner.
    Executes Sense -> Think -> Act loop for model retraining.
    """

    def __init__(
        self,
        interval_seconds: int = 60,
        trainer: Optional[ITrainer] = None, # Injected trainer implementation
        model_factory = None # Function to create new predictor instances
    ):
        self.interval_seconds = interval_seconds
        self.trainer = trainer
        self.model_factory = model_factory
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._stats = {
            "last_run": None,
            "total_runs": 0,
            "retrains_triggered": 0,
            "errors": 0,
            "last_error": None
        }

    def start(self):
        """Start the background worker thread."""
        if self._is_running:
            logger.warning("LearningWorker already running.")
            return

        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="LearningWorkerThread")
        self._thread.start()
        logger.info(f"🚀 LearningWorker started (Interval: {self.interval_seconds}s)")

    def stop(self):
        """Stop the background worker thread gracefully."""
        if not self._is_running:
            return

        logger.info("🛑 LearningWorker stopping...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._is_running = False
        logger.info("✅ LearningWorker stopped.")

    def get_stats(self) -> dict:
        """Get worker statistics."""
        return self._stats

    def _run_loop(self):
        """Main worker loop."""
        while not self._stop_event.is_set():
            try:
                self._execute_cycle()
                self._stats["total_runs"] += 1
                self._stats["last_run"] = datetime.utcnow().isoformat()
            except Exception as e:
                self._stats["errors"] += 1
                self._stats["last_error"] = str(e)
                logger.error(f"❌ LearningWorker error: {e}", exc_info=True)

            # Wait for next interval or stop signal
            if self._stop_event.wait(self.interval_seconds):
                break

    def _execute_cycle(self):
        """
        Execute one complete check-and-retrain cycle.
        Creates fresh DB session for each cycle to avoid stale state.
        """
        # Session management: create new session for this unit of work
        db = SessionLocal()
        
        try:
            # 1. Setup Repositories & Services
            settings_repo = SystemSettingsRepository(db)
            runner = LearningAgentRunner(settings_repo)
            
            # 2. Sense & Think (Runner Decision)
            decision, context = runner.run_cycle()
            logger.info(f"🧠 Learning Agent Decision: {decision} ({context['reason']})")

            # 3. Act (Retraining) if needed
            if decision in [TrainingDecision.INCREMENTAL_TRAINING, TrainingDecision.FULL_RETRAINING]:
                if not self.trainer:
                    logger.warning("⚠️ Retraining needed but no Trainer configured. Skipping.")
                    return

                self._perform_retraining(db, decision, settings_repo)
                self._stats["retrains_triggered"] += 1

        finally:
            db.close()

    def _perform_retraining(self, db, decision: TrainingDecision, settings_repo):
        """
        Orchestrate the retraining process:
        Formatter -> Trainer -> Versioning -> HotSwap
        """
        logger.info(f"🏋️ Starting {decision.value}...")
        
        # Repos needed for formatting & versioning
        pred_repo = AgentPredictionRepository(db)
        log_repo = DailyLogRepository(db)
        version_repo = ModelVersionRepository(db)
        model_registry = ModelRegistry()

        # A. Format Dataset
        formatter = DatasetFormatterService(pred_repo, log_repo)
        dataset_paths = formatter.generate_dataset()
        logger.info(f"   📂 Dataset ready: {dataset_paths['train_file']}")

        # B. Retrain Model
        # Map Decision -> Mode
        from backend.domain.enums.enums import TrainingMode
        mode = TrainingMode.INCREMENTAL if decision == TrainingDecision.INCREMENTAL_TRAINING else TrainingMode.FULL
        
        settings = settings_repo.get_settings()
        
        # Execute Training (Delegated to ITrainer)
        # Note: dataset_reference passed as train_file path
        train_result = self.trainer.retrain(
            mode=mode,
            dataset_reference=dataset_paths['train_file'],
            settings=settings
        )
        
        if not train_result.get("success"):
            logger.error(f"   ❌ Training failed: {train_result.get('error')}")
            return

        # C. Versioning
        new_version = ModelVersionEntity(
            version_number=train_result["model_version"],
            training_mode=mode.value,
            dataset_size=train_result["metrics"]["train_samples"],
            model_file_path=train_result["model_path"],
            accuracy=train_result["metrics"].get("accuracy") or train_result["metrics"].get("test_r2_score"), # Adapt based on metric
            created_at=datetime.utcnow()
        )
        version_repo.add(new_version)
        logger.info(f"   fw Version {new_version.version_number} saved.")

        # D. Hot Swapping
        if self.model_factory:
            try:
                # Create empty predictor instance
                new_predictor = self.model_factory()
                # Load weights
                new_predictor.load_model(new_version.model_file_path)
                # Swap
                model_registry.load_new_model(new_predictor)
            except Exception as e:
                 logger.error(f"   ⚠️ Hot-swap failed: {e}")
                 # Don't fail the whole cycle, model is saved on disk at least
        
        # E. Update System State (Reset counters)
        settings_repo.record_retrain_success()
        logger.info("   ✅ Cycle complete. System counters reset.")
