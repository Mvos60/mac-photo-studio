from __future__ import annotations

from pathlib import Path

from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_prompts import prompt_day, prompt_project, prompt_year


def prompt_folder(label: str) -> Path:
    return Path(input(f"{label}: ").strip()).expanduser()


def collect_import_session(default_year: int) -> ImportSessionRequest:
    year = prompt_year(default_year)
    project = prompt_project()
    day = prompt_day()
    raw_folder = prompt_folder("RAW folder")
    jpeg_folder = prompt_folder("JPEG folder")

    return ImportSessionRequest(
        year=year,
        project=project,
        day=day,
        raw_folder=raw_folder,
        jpeg_folder=jpeg_folder,
    )
