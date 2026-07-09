from pathlib import Path

from mps.models.card import CardScanResult
from mps.services.import_card_report import build_card_report
from mps.services.import_card_selector import ImportCardSelection


def card(raw: int = 0, jpg: int = 0):
    return CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
        raw_count=raw,
        jpeg_count=jpg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpg),
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=0,
    )


def test_build_card_report():
    report = build_card_report(
        ImportCardSelection(
            raw_card=card(raw=250),
            jpeg_card=card(jpg=250),
            warnings=[],
        )
    )

    assert "Searching for photo cards..." in report
    assert "RAW files : 250" in report
    assert "JPEG files: 250" in report


def test_build_card_report_with_warning():
    report = build_card_report(
        ImportCardSelection(
            raw_card=None,
            jpeg_card=None,
            warnings=["No RAW card found"],
        )
    )

    assert "Warnings" in report
    assert "No RAW card found" in report
