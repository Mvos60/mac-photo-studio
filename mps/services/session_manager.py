"""Historical ImportSession persistence service.

This service belongs to the pre-ImportMediaSession session architecture.

Current sequential import recovery uses import_media_session_store and
import_media_resume_validator.
"""

import json
from dataclasses import asdict
from pathlib import Path

from mps.models.import_session import ImportSession


class ImportSessionManager:
    def __init__(self, session_root: str | Path):
        self.session_root = Path(session_root)

    def start_session(
        self,
        *,
        camera: str | None = None,
        card_label: str | None = None,
        files_discovered: int = 0,
    ) -> ImportSession:
        self.session_root.mkdir(parents=True, exist_ok=True)
        return ImportSession(
            camera=camera,
            card_label=card_label,
            files_discovered=files_discovered,
        )

    def save_session(self, session: ImportSession) -> Path:
        self.session_root.mkdir(parents=True, exist_ok=True)
        path = self.session_root / f"{session.session_id}.json"
        path.write_text(
            json.dumps(asdict(session), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def load_session(self, session_id: str) -> ImportSession:
        path = self.session_root / f"{session_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return ImportSession(**data)

    def finish_session(
        self,
        session: ImportSession,
        *,
        status: str = "completed",
        files_imported: int | None = None,
        files_skipped: int | None = None,
        conflicts: int | None = None,
        manifest_path: str | Path | None = None,
    ) -> ImportSession:
        if files_imported is not None:
            session.files_imported = files_imported
        if files_skipped is not None:
            session.files_skipped = files_skipped
        if conflicts is not None:
            session.conflicts = conflicts
        if manifest_path is not None:
            session.manifest_path = str(manifest_path)

        session.finish(status=status)
        return session
