from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Iterable, Mapping

EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


def parse_datetime_original(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, EXIF_DATETIME_FORMAT)
    except ValueError:
        return None


def read_datetime_original(source_paths: Iterable[Path]) -> dict[Path, datetime | None]:
    """Read DateTimeOriginal for unique paths with one ExifTool process."""
    paths = tuple(sorted(set(source_paths)))
    result = {path: None for path in paths}
    if not paths:
        return result
    normalized = {path.expanduser().resolve(strict=False): path for path in paths}
    try:
        completed = subprocess.run(
            ["exiftool", "-j", "-DateTimeOriginal", *(str(path) for path in paths)],
            check=False, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return result
    if completed.returncode != 0:
        return result
    try:
        records = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        return result
    if not isinstance(records, list):
        return result
    for record in records:
        if not isinstance(record, dict):
            continue
        source_file = record.get("SourceFile")
        if not isinstance(source_file, str):
            continue
        requested = normalized.get(Path(source_file).expanduser().resolve(strict=False))
        if requested is not None:
            result[requested] = parse_datetime_original(record.get("DateTimeOriginal"))
    return result


def resolve_candidate_captured_at(
    source_paths: Iterable[Path],
    metadata: Mapping[Path, datetime | None],
) -> tuple[datetime | None, bool]:
    values = {value for path in source_paths if (value := metadata.get(path)) is not None}
    if len(values) > 1:
        return None, True
    return (next(iter(values)), False) if values else (None, False)
