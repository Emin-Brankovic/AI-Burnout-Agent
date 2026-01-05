"""
Burnout Prediction Worker

Background worker that runs Burnout Prediction Agent in a loop.

⭐ THIS IS A KEY CLASS - shows how the agent runs in background!
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable

from sqlalchemy.orm import Session
from backend.application.agents.burnout_prediction_agent_runner import (
    BurnoutPredictionAgentRunner,
    PredictionResult
)
from backend.application.services.queue_service import DailyLogQueueService
from backend.application.services.prediction_service import get_prediction_service
from backend.application.services.review_service import get_notification_service
from backend.infrastructure.persistence.repositories.agent_prediction_repository import AgentPredictionRepository
from backend.infrastructure.persistence.repositories.daily_log_repository import DailyLogRepository
from backend.infrastructure.persistence.repositories.employee_repository import EmployeeRepository


class BurnoutPredictionWorker:
    """
    Background worker for Burnout Prediction Agent.

    Runs agent tick() every N seconds.

    IMPORTANT:
    - Worker IS THIN - only calls runner.step_async()
    - Worker DOES NOT CONTAIN business logic
    - Worker is only responsible for: loop + delay + error handling
    """

    def __init__(
        self,
        runner: BurnoutPredictionAgentRunner,
        tick_interval_seconds: int = 5,
        name: str = "BurnoutPredictionWorker"
    ):
        """
        Initialize the worker.

        Args:
            runner: Agent runner instance
            tick_interval_seconds: How often agent ticks (seconds)
            name: Worker name for logging
        """
        self.runner = runner
        self.tick_interval = tick_interval_seconds
        self.name = name

        # State tracking
        self._is_running = False
        self._tick_count = 0
        self._last_tick_at: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None

        # Statistics
        self._processed_count = 0
        self._error_count = 0

        # Callbacks (for real-time events)
        self._result_callback: Optional[Callable[[PredictionResult], Awaitable[None]]] = None
        self._error_callback: Optional[Callable[[Exception], Awaitable[None]]] = None

    # ========================================
    # WORKER LIFECYCLE
    # ========================================

    def start(self):
        """
        Start worker (non-blocking).
        """
        if self._is_running:
            print(f"⚠️  {self.name} already running")
            return

        self._is_running = True
        self.runner.start()

        # Start async task
        self._task = asyncio.create_task(self._run_loop())

        print(f"✅ {self.name} started (tick every {self.tick_interval}s)")

    def stop(self):
        """
        Stop worker (graceful shutdown).
        """
        if not self._is_running:
            return

        self._is_running = False
        self.runner.stop()

        if self._task:
            self._task.cancel()

        print(f"🛑 {self.name} stopped")
        print(f"   Total ticks: {self._tick_count}")
        print(f"   Processed: {self._processed_count}")
        print(f"   Errors: {self._error_count}")

    @property
    def is_running(self) -> bool:
        """Check if worker is running"""
        return self._is_running

    @property
    def tick_count(self) -> int:
        """Number of ticks so far"""
        return self._tick_count

    @property
    def last_tick_at(self) -> Optional[datetime]:
        """Time of last tick"""
        return self._last_tick_at

    @property
    def processed_count(self) -> int:
        """Number of successfully processed logs"""
        return self._processed_count

    @property
    def error_count(self) -> int:
        """Number of errors encountered"""
        return self._error_count

    # ========================================
    # AGENT LOOP (private method)
    # ========================================

    async def _run_loop(self):
        """
        Main agent loop.

        while running:
            1. Call runner.step_async()
            2. If result exists → emit event
            3. Delay
            4. Repeat
        """
        print(f"🔄 {self.name} loop started")

        while self._is_running:
            try:
                # ⭐ AGENT TICK - call runner
                result = await self.runner.step_async()

                self._tick_count += 1
                self._last_tick_at = datetime.utcnow()

                if result:
                    # Agent processed a daily log!
                    self._processed_count += 1

                    # print(f"✅ Agent tick #{self._tick_count}: "
                    #       f"Employee {result.employee_id} - "
                    #       f"{result.risk_level} ({result.burnout_rate:.1%})")

                    # Emit event (if callback registered)
                    if self._result_callback:
                        try:
                            await self._result_callback(result)
                        except Exception as cb_error:
                            print(f"⚠️ Error in result callback: {cb_error}")
                else:
                    # No work - agent is idle
                    # (don't log to avoid console spam)
                    pass

            except Exception as e:
                # Error handling - log but continue
                self._error_count += 1
                print(f"❌ {self.name} error in tick #{self._tick_count}: {e}")

                # Emit error event
                if self._error_callback:
                    try:
                        await self._error_callback(e)
                    except Exception as cb_error:
                        print(f"⚠️ Error in error callback: {cb_error}")

                # Print traceback for debugging
                import traceback
                traceback.print_exc()

            # Delay before next tick
            await asyncio.sleep(self.tick_interval)

        print(f"🛑 {self.name} loop stopped")

    # ========================================
    # EVENT CALLBACKS (for real-time updates)
    # ========================================

    def on_result(self, callback: Callable[[PredictionResult], Awaitable[None]]):
        """
        Register callback for prediction results.

        Args:
            callback: Async function that receives PredictionResult

        Usage:
            worker.on_result(emit_to_websocket)
            worker.on_result(send_notification)
        """
        self._result_callback = callback

    def on_error(self, callback: Callable[[Exception], Awaitable[None]]):
        """
        Register callback for errors.

        Args:
            callback: Async function that receives Exception

        Usage:
            worker.on_error(log_to_sentry)
        """
        self._error_callback = callback

    # ========================================
    # BATCH PROCESSING
    # ========================================

    async def process_batch_now(self, batch_size: int = 10) -> list[PredictionResult]:
        """
        Process batch of logs immediately (outside regular loop).

        Args:
            batch_size: Number of logs to process

        Returns:
            List of prediction results
        """
        print(f"📦 Processing batch of {batch_size} logs...")

        try:
            results = await self.runner.process_batch(batch_size)
            self._processed_count += len(results)

            print(f"✅ Batch processing complete: {len(results)} logs processed")

            # Emit events for each result
            if self._result_callback:
                for result in results:
                    try:
                        await self._result_callback(result)
                    except Exception as e:
                        print(f"⚠️ Error in batch result callback: {e}")

            return results

        except Exception as e:
            self._error_count += 1
            print(f"❌ Error in batch processing: {e}")

            if self._error_callback:
                await self._error_callback(e)

            raise

    # ========================================
    # STATISTICS
    # ========================================

    async def get_stats(self) -> dict:
        """Get worker statistics"""
        queue_stats = await self.runner.get_queue_stats()

        return {
            "name": self.name,
            "is_running": self.is_running,
            "tick_count": self.tick_count,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at else None,
            "tick_interval_seconds": self.tick_interval,
            "queue": queue_stats,
        }

    # ========================================
    # DYNAMIC CONFIGURATION
    # ========================================

    def set_tick_interval(self, seconds: int):
        """
        Update tick interval dynamically.

        Args:
            seconds: New tick interval in seconds
        """
        if seconds < 1:
            raise ValueError("Tick interval must be at least 1 second")

        self.tick_interval = seconds
        print(f"🔧 Tick interval updated to {seconds}s")

    # def set_confidence_threshold(self, threshold: float):
    #     """
    #     Update confidence threshold dynamically.
    #
    #     Args:
    #         threshold: New threshold (0.0 - 1.0)
    #     """
    #     self.runner.set_confidence_threshold(threshold)

    # ========================================
    # CONTEXT MANAGER SUPPORT
    # ========================================

    async def __aenter__(self):
        """Async context manager entry"""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.stop()
        return False



# ============================================================================
# Factory function for dependency injection
# ============================================================================

def get_prediction_worker(db: Session, tick_interval: int = 5) -> BurnoutPredictionWorker:
    """
    Factory function for creating BurnoutPredictionWorker with all dependencies.
    """
    # 1. Repositories
    prediction_repo = AgentPredictionRepository(db)
    daily_log_repo = DailyLogRepository(db)
    employee_repo = EmployeeRepository(db)

    # 2. Services
    queue_service = DailyLogQueueService(db)
    prediction_service = get_prediction_service(
        prediction_repository=prediction_repo,
        daily_log_repository=daily_log_repo,
        employee_repository=employee_repo
    )
    notification_service = get_notification_service()

    # 3. Agent Runner
    runner = BurnoutPredictionAgentRunner(
        queue_service=queue_service,
        prediction_service=prediction_service,
        email_notification_service=notification_service
    )

    # 4. Worker
    return BurnoutPredictionWorker(
        runner=runner,
        tick_interval_seconds=tick_interval
    )


if __name__ == "__main__":
    print("✅ BurnoutPredictionWorker loaded")
    print("   - Runs Burnout Prediction Agent in background loop")
    print("   - Tick interval: configurable")
    print("   - Graceful start/stop")
    print("   - Real-time callbacks support")
