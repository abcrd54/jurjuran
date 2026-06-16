import logging
import time
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class Step(str, Enum):
    SCRAPE = "scrape"
    SCRIPT = "script"
    TTS = "tts"
    MEDIA = "media"
    COMPOSE = "compose"
    CAPTION = "caption"
    DONE = "done"
    ERROR = "error"


STEP_ORDER = [Step.SCRAPE, Step.SCRIPT, Step.TTS, Step.MEDIA, Step.COMPOSE, Step.CAPTION, Step.DONE]
STEP_WEIGHTS = {
    Step.SCRAPE: 10,
    Step.SCRIPT: 10,
    Step.TTS: 10,
    Step.MEDIA: 20,
    Step.COMPOSE: 35,
    Step.CAPTION: 15,
    Step.DONE: 0,
}


@dataclass
class ProgressTracker:
    request_id: str
    current_step: Step = Step.SCRAPE
    progress: float = 0.0
    message: str = "Starting..."
    details: dict = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    error: str | None = None

    def update(self, step: Step, message: str, details: dict = None):
        self.current_step = step
        self.message = message
        if details:
            self.details.update(details)

        step_index = STEP_ORDER.index(step) if step in STEP_ORDER else 0
        base_progress = sum(STEP_WEIGHTS[s] for s in STEP_ORDER[:step_index])
        self.progress = min(base_progress, 100)

        elapsed = time.time() - self.start_time
        logger.info(f"[{self.request_id}] {step.value}: {message} ({self.progress:.0f}%, {elapsed:.1f}s)")

    def set_sub_progress(self, sub_progress: float):
        step_weight = STEP_WEIGHTS.get(self.current_step, 0)
        step_index = STEP_ORDER.index(self.current_step) if self.current_step in STEP_ORDER else 0
        base_progress = sum(STEP_WEIGHTS[s] for s in STEP_ORDER[:step_index])
        self.progress = min(base_progress + step_weight * sub_progress, 100)

    def finish(self):
        self.current_step = Step.DONE
        self.progress = 100
        self.message = "Video selesai!"
        elapsed = time.time() - self.start_time
        logger.info(f"[{self.request_id}] Done in {elapsed:.1f}s")

    def fail(self, error: str):
        self.current_step = Step.ERROR
        self.error = error
        self.message = f"Error: {error}"
        logger.error(f"[{self.request_id}] Error: {error}")

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "step": self.current_step.value,
            "progress": round(self.progress, 1),
            "message": self.message,
            "details": self.details,
            "elapsed": round(time.time() - self.start_time, 1),
            "error": self.error,
        }


class ProgressManager:
    def __init__(self):
        self._trackers: dict[str, ProgressTracker] = {}

    def create(self, request_id: str) -> ProgressTracker:
        tracker = ProgressTracker(request_id=request_id)
        self._trackers[request_id] = tracker
        return tracker

    def get(self, request_id: str) -> ProgressTracker | None:
        return self._trackers.get(request_id)

    def remove(self, request_id: str):
        self._trackers.pop(request_id, None)


progress_manager = ProgressManager()
