from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_wizard_runner import run_interactive_import


def card():
    return CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
        raw_count=42,
        jpeg_count=42,
        heif_count=0,
        video_count=0,
        pair_count=42,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=0,
    )


def test_run_interactive_import(monkeypatch):
    monkeypatch.setattr(
        "mps.services.import_wizard_runner.discover_import_cards",
        lambda settings: ImportCardSelection(
            raw_card=card(),
            jpeg_card=card(),
            warnings=[],
        ),
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_year",
        lambda default: 2026,
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_project",
        lambda: "Adriatic",
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_day",
        lambda: "03_Slovenia",
    )

    session = run_interactive_import(Settings({}))

    assert session.year == 2026
    assert session.project == "Adriatic"
    assert session.day == "03_Slovenia"

    assert session.raw_folder == Path("/media/card")
    assert session.jpeg_folder == Path("/media/card")
