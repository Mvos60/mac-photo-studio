from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_planner import create_import_plan
from mps.services.import_wizard_ui import (
    build_import_plan_preview,
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


def test_build_import_plan_preview(tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (raw / "DSC0002.ARW").write_bytes(b"raw")
    (jpeg / "DSC0001.JPG").write_bytes(b"jpeg")

    settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )

    plan = create_import_plan(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpeg,
        settings=settings,
    )

    preview = build_import_plan_preview(plan)

    assert "Import Plan Preview" in preview
    assert f"Destination : {plan.destination}" in preview
    assert "Pairs       : 1" in preview
    assert "RAW only    : 1" in preview
    assert "JPEG only   : 0" in preview
    assert "Total files : 3" in preview
    assert "Size bytes  : 10" in preview
    assert "Warnings" in preview
    assert "- 1 RAW file(s) have no matching JPEG" in preview
