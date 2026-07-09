from __future__ import annotations

from datetime import datetime

from mps.config import Settings
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_card_discovery import discover_import_cards
from mps.services.import_prompts import (
    prompt_day,
    prompt_project,
    prompt_year,
)
from mps.services.import_wizard_ui import build_wizard_intro


def run_interactive_import(settings: Settings) -> ImportSessionRequest:
    selection = discover_import_cards(settings)

    print(build_wizard_intro(selection))
    print()

    year = prompt_year(datetime.now().year)
    project = prompt_project()
    day = prompt_day()

    raw_folder = (
        selection.raw_card.root
        if selection.raw_card is not None
        else None
    )

    jpeg_folder = (
        selection.jpeg_card.root
        if selection.jpeg_card is not None
        else None
    )

    return ImportSessionRequest(
        year=year,
        project=project,
        day=day,
        raw_folder=raw_folder,
        jpeg_folder=jpeg_folder,
    )
