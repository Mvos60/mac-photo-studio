from __future__ import annotations

import json
from pathlib import Path

from mps.models.import_media_session import ImportMediaSession


def save_import_media_session(
    session: ImportMediaSession,
    path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "session_id": session.session_id,
        "source_fingerprints": sorted(
            session.source_fingerprints
        ),
        "processed_source_files": [
            str(path)
            for path in session.processed_source_files
        ],
    }

    output.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output


def load_import_media_session(
    path: str | Path,
) -> ImportMediaSession:
    data = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    return ImportMediaSession(
        session_id=data.get("session_id"),
        sources=[],
        source_fingerprints=set(
            data.get("source_fingerprints", [])
        ),
        processed_source_files=[
            Path(value)
            for value in data.get(
                "processed_source_files",
                [],
            )
        ],
    )
