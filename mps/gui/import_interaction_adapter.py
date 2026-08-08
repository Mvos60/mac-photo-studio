from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Event, Lock

from mps.models.import_photo_selection import ImportPhotoSelectionResponse
from mps.models.import_workflow import (
    ImportEvent,
    ImportEventType,
    ImportInteractionResponse,
    ImportRequest,
    ImportResponse,
)


@dataclass(slots=True)
class PendingImportInteraction:
    request: ImportRequest
    _ready: Event = field(default_factory=Event, init=False, repr=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _response: ImportInteractionResponse | None = field(
        default=None, init=False
    )

    def respond(self, response: ImportInteractionResponse) -> None:
        if not isinstance(
            response, (ImportResponse, ImportPhotoSelectionResponse)
        ):
            raise TypeError("Import interaction requires a typed response")
        with self._lock:
            if self._response is None:
                self._response = response
                self._ready.set()

    def wait(self, cancellation: Event) -> ImportInteractionResponse:
        while not self._ready.wait(0.1):
            if cancellation.is_set():
                return ImportResponse.CANCEL_PRESERVE_STATE
        with self._lock:
            return self._response or ImportResponse.ALL_MEDIA_READY


class GuiImportInteractionAdapter:
    """Bridge a worker request to a response supplied on the GUI thread."""

    def __init__(
        self,
        event_sink: Callable[[ImportEvent], None],
        cancellation: Event,
    ) -> None:
        self._event_sink = event_sink
        self._cancellation = cancellation

    def request(
        self, request: ImportRequest
    ) -> ImportInteractionResponse:
        if self._cancellation.is_set():
            return ImportResponse.CANCEL_PRESERVE_STATE
        pending = PendingImportInteraction(request)
        self._event_sink(ImportEvent(
            ImportEventType.INTERACTION_REQUESTED,
            {"interaction": pending, "request": request},
        ))
        return pending.wait(self._cancellation)
