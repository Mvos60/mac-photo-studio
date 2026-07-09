from __future__ import annotations

from pathlib import Path

from mps.models.import_session_request import ImportSessionRequest


def build_import_session(
    *,
    year: int,
    project: str,
    day: str,
    raw_folder: str | Path,
    jpeg_folder: str | Path,
) -> ImportSessionRequest:
    return ImportSessionRequest(
        year=year,
        project=project,
        day=day,
        raw_folder=Path(raw_folder).expanduser(),
        jpeg_folder=Path(jpeg_folder).expanduser(),
    )
