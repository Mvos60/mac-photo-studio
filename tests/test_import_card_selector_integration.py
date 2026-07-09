from pathlib import Path

from mps.models.card import CardScanResult
from mps.services.import_card_selector import select_import_cards


def card(root: str, raw: int = 0, jpg: int = 0):
    return CardScanResult(
        root=Path(root),
        dcim_path=Path(root) / "DCIM",
        raw_count=raw,
        jpeg_count=jpg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpg),
        orphan_raw_count=max(raw - jpg, 0),
        orphan_jpeg_count=max(jpg - raw, 0),
        other_count=0,
        total_size_bytes=123456,
    )


def test_single_dual_card():
    c = card("/media/card", raw=500, jpg=500)

    result = select_import_cards([c])

    assert result.raw_card == c
    assert result.jpeg_card == c
    assert result.warnings == []


def test_two_card_workflow():
    raw = card("/media/raw", raw=800)
    jpg = card("/media/jpg", jpg=800)

    result = select_import_cards([raw, jpg])

    assert result.raw_card == raw
    assert result.jpeg_card == jpg
