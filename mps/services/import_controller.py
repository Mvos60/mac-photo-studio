from __future__ import annotations

from collections.abc import Callable
from enum import Enum
import logging
from queue import Empty, Queue
from threading import Event, Lock, Thread

from mps.models.import_workflow import ImportEvent, ImportEventType


LOGGER = logging.getLogger(__name__)


class ImportControllerStatus(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    WAITING_FOR_MEDIA = "waiting_for_media"
    CANCELLING = "cancelling"
    FAILED = "failed"
    COMPLETED = "completed"


class ImportAlreadyActiveError(RuntimeError):
    """Raised when a second import is started while one is active."""


ImportRunner = Callable[[Callable[[ImportEvent], None], Event], object]


class ImportController:
    """Run one import worker and expose its typed events through a queue."""

    def __init__(self) -> None:
        self._events: Queue[ImportEvent] = Queue()
        self._cancel_event = Event()
        self._worker: Thread | None = None
        self._status = ImportControllerStatus.IDLE
        self._lock = Lock()

    @property
    def status(self) -> ImportControllerStatus:
        with self._lock:
            return self._status

    @property
    def state(self) -> ImportControllerStatus:
        return self.status

    @property
    def is_active(self) -> bool:
        return self.worker_alive

    @property
    def worker_alive(self) -> bool:
        worker = self._worker
        return worker is not None and worker.is_alive()

    @property
    def cancellation_event(self) -> Event:
        return self._cancel_event

    def start(self, runner: ImportRunner) -> None:
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                raise ImportAlreadyActiveError(
                    "An import worker is already active"
                )

            self._cancel_event = Event()
            self._status = ImportControllerStatus.STARTING
            worker = Thread(
                target=self._run_worker,
                args=(runner,),
                name="mps-import-worker",
                daemon=False,
            )
            self._worker = worker
            worker.start()

    def _run_worker(self, runner: ImportRunner) -> None:
        failed_published = False

        def event_sink(event: ImportEvent) -> None:
            nonlocal failed_published
            if not isinstance(event, ImportEvent):
                raise TypeError("Import event sink requires ImportEvent")
            if event.type is ImportEventType.FAILED:
                failed_published = True
            self._events.put(event)

        try:
            runner(event_sink, self._cancel_event)
        except BaseException as exc:
            LOGGER.exception("Import worker failed")
            if not failed_published:
                event_sink(ImportEvent(
                    ImportEventType.FAILED,
                    {
                        "code": "worker_exception",
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                ))

    def drain_events(self) -> list[ImportEvent]:
        events: list[ImportEvent] = []
        while True:
            try:
                event = self._events.get_nowait()
            except Empty:
                break
            self._apply_event_status(event)
            events.append(event)
        return events

    get_pending_events = drain_events

    def _apply_event_status(self, event: ImportEvent) -> None:
        running_events = {
            ImportEventType.SESSION_STARTED,
            ImportEventType.MEDIA_DISCOVERY_STARTED,
            ImportEventType.BATCH_STARTED,
            ImportEventType.BATCH_PLANNED,
            ImportEventType.RECONCILIATION_STARTED,
        }
        with self._lock:
            if event.type in running_events:
                self._status = ImportControllerStatus.RUNNING
            elif event.type is ImportEventType.WAITING_FOR_MEDIA:
                self._status = ImportControllerStatus.WAITING_FOR_MEDIA
            elif event.type is ImportEventType.FAILED:
                self._status = ImportControllerStatus.FAILED
            elif event.type is ImportEventType.COMPLETED:
                self._status = ImportControllerStatus.COMPLETED

    def request_cancel(self) -> None:
        self._cancel_event.set()
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                self._status = ImportControllerStatus.CANCELLING

    def join(self, timeout: float | None = None) -> None:
        worker = self._worker
        if worker is not None:
            worker.join(timeout)
