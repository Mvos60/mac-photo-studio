from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class ImportSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=utc_now_iso)
    ended_at: str | None = None
    status: str = "started"
    camera: str | None = None
    card_label: str | None = None
    manifest_path: str | None = None
    files_discovered: int = 0
    files_imported: int = 0
    files_skipped: int = 0
    conflicts: int = 0

    def finish(self, status: str = "completed") -> None:
        self.status = status
        self.ended_at = utc_now_iso()
