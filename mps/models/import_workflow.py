from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol


class ImportEventType(str, Enum):
    SESSION_STARTED = "session_started"
    MEDIA_DISCOVERY_STARTED = "media_discovery_started"
    MEDIA_DISCOVERED = "media_discovered"
    WAITING_FOR_MEDIA = "waiting_for_media"
    BATCH_STARTED = "batch_started"
    BATCH_PLANNED = "batch_planned"
    BATCH_COMPLETED = "batch_completed"
    PROGRESS = "progress"
    RECONCILIATION_STARTED = "reconciliation_started"
    RECONCILIATION_COMPLETED = "reconciliation_completed"
    WARNING = "warning"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ImportEvent:
    """Structured notification emitted at a reliable workflow boundary."""

    type: ImportEventType
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "payload",
            MappingProxyType(dict(self.payload)),
        )


class ImportRequestType(str, Enum):
    NEXT_MEDIA_ACTION = "next_media_action"


class ImportWaitingReason(str, Enum):
    PROCESSED_MEDIA_MOUNTED = "processed_media_mounted"
    NO_MEDIA_MOUNTED = "no_media_mounted"
    BATCH_COMPLETED = "batch_completed"


@dataclass(frozen=True, slots=True)
class ImportRequest:
    type: ImportRequestType
    reason: ImportWaitingReason


class ImportResponse(str, Enum):
    RESCAN_MEDIA = "rescan_media"
    ALL_MEDIA_READY = "all_media_ready"


class ImportInteractionAdapter(Protocol):
    def request(self, request: ImportRequest) -> ImportResponse:
        """Return one of the supported import workflow responses."""
