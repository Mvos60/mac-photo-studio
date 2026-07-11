from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.import_media_report import build_media_report


def _card(
    root: str,
    *,
    raw: int = 0,
    jpeg: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=Path(root),
        dcim_path=Path(root) / "DCIM",
        raw_count=raw,
        jpeg_count=jpeg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0),
        other_count=0,
        total_size_bytes=0,
    )


def test_build_media_report_for_single_raw_card():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/raw", raw=500),
        ]
    )

    output = build_media_report(selection)

    assert "Photo sources found: 1" in output
    assert "Source 1" in output
    assert "/media/raw" in output
    assert "RAW files : 500" in output
    assert "JPEG files: 0" in output


def test_build_media_report_for_two_cards():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/raw", raw=500),
            _card("/media/jpeg", jpeg=500),
        ]
    )

    output = build_media_report(selection)

    assert "Photo sources found: 2" in output
    assert "Source 1" in output
    assert "Source 2" in output
    assert "/media/raw" in output
    assert "/media/jpeg" in output
    assert "RAW files : 500" in output
    assert "JPEG files: 500" in output


def test_build_media_report_for_mixed_card():
    selection = ImportMediaSelection(
        sources=[
            _card(
                "/media/mixed",
                raw=500,
                jpeg=500,
            ),
        ]
    )

    output = build_media_report(selection)

    assert "Photo sources found: 1" in output
    assert "Pairs     : 500" in output
    assert "Current media inventory" in output
    assert "RAW files : 500" in output
    assert "JPEG files: 500" in output


def test_build_media_report_when_empty():
    selection = ImportMediaSelection(sources=[])

    output = build_media_report(selection)

    assert "Searching for photo media..." in output
    assert "No photo media found." in output
