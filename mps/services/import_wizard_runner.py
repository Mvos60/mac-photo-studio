"""Historical card-selection import wizard runner.

This runner belongs to the original RAW-card/JPEG-card workflow and is not a
current production entry point.

New interactive import development must use
mps.services.import_media_wizard_runner.
"""

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
from mps.services.import_request_planner import create_plan_from_request
from mps.services.import_wizard_ui import (
    build_import_plan_preview,
    build_import_summary,
    build_wizard_intro,
)


def run_interactive_import(settings: Settings) -> ImportSessionRequest | None:
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

    request = ImportSessionRequest(
        year=year,
        project=project,
        day=day,
        raw_folder=raw_folder,
        jpeg_folder=jpeg_folder,
    )

    print()
    print(build_import_summary(request))
    print()

    answer = input("Continue with this import? [Y/n]: ").strip().lower()

    if answer in {"n", "no"}:
        print("Import cancelled.")
        return None

    plan = create_plan_from_request(request, settings)

    print()
    print(build_import_plan_preview(plan))
    print()

    answer = input("Accept this import plan? [Y/n]: ").strip().lower()

    if answer in {"n", "no"}:
        print("Import plan rejected.")
        return None

    return request
