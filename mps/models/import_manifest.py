from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ManifestFileEntry:
    source_path: str
    destination_path: str
    sha256: str
    action: str
    status: str
    bytes: int


@dataclass(slots=True)
class ImportManifest:
    session_id: str
    created_at: str
    project: str
    day_session: str
    mps_version: str
    files: list[ManifestFileEntry] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(entry.bytes for entry in self.files)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["file_count"] = self.file_count
        data["total_bytes"] = self.total_bytes
        return data


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_session_id() -> str:
    return str(uuid4())


def manifest_path(destination_root: str | Path, session_id: str) -> Path:
    return Path(destination_root) / "manifest" / f"import_manifest_{session_id}.json"
