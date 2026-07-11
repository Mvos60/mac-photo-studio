from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_wizard_ui import (
    build_import_summary,
    build_wizard_intro,
)


def card():
    return CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
        raw_count=100,
        jpeg_count=100,
        heif_count=0,
        video_count=0,
        pair_count=100,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=0,
    )


def test_build_wizard_intro():
    intro = build_wizard_intro(
        ImportCardSelection(
            raw_card=card(),
            jpeg_card=card(),
            warnings=[],
        )
    )

    assert "Mac Photo Studio Import Wizard" in intro
    assert "Searching for photo cards..." in intro
    assert "RAW files : 100" in intro
    assert "JPEG files: 100" in intro


def test_build_import_summary():
    summary = build_import_summary(
        ImportSessionRequest(
            year=2026,
            project="Adriatic",
            day="03_Slovenia",
            raw_folder=Path("/media/raw"),
            jpeg_folder=Path("/media/jpeg"),
        )
    )

    assert "Import Summary" in summary
    assert "Year        : 2026" in summary
    assert "Project     : Adriatic" in summary
    assert "Day/session : 03_Slovenia" in summary
    assert "RAW folder  : /media/raw" in summary
    assert "JPEG folder : /media/jpeg" in summary
