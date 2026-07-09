from pathlib import Path

from mps.models.card import CardScanResult
from mps.services.import_card_selector import select_import_cards


def _card(
    root: str,
    raw_count: int = 0,
    jpeg_count: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=Path(root),
        dcim_path=Path(root) / "DCIM",
        raw_count=raw_count,
        jpeg_count=jpeg_count,
        heif_count=0,
        video_count=0,
        pair_count=min(raw_count, jpeg_count),
        orphan_raw_count=max(raw_count - jpeg_count, 0),
        orphan_jpeg_count=max(jpeg_count - raw_count, 0),
        other_count=0,
        total_size_bytes=0,
    )


def test_select_import_cards_finds_raw_and_jpeg_cards():
    raw = _card("/media/raw", raw_count=10)
    jpeg = _card("/media/jpeg", jpeg_count=10)

    selection = select_import_cards([raw, jpeg])

    assert selection.raw_card == raw
    assert selection.jpeg_card == jpeg
    assert selection.warnings == []


def test_select_import_cards_can_use_same_card_for_raw_and_jpeg():
    card = _card("/media/card", raw_count=10, jpeg_count=10)

    selection = select_import_cards([card])

    assert selection.raw_card == card
    assert selection.jpeg_card == card
    assert selection.warnings == []


def test_select_import_cards_reports_missing_cards():
    selection = select_import_cards([])

    assert selection.raw_card is None
    assert selection.jpeg_card is None
    assert selection.warnings == [
        "No RAW card found",
        "No JPEG card found",
    ]


def test_select_import_cards_warns_about_multiple_candidates():
    raw1 = _card("/media/raw1", raw_count=10)
    raw2 = _card("/media/raw2", raw_count=20)
    jpeg1 = _card("/media/jpeg1", jpeg_count=10)
    jpeg2 = _card("/media/jpeg2", jpeg_count=20)

    selection = select_import_cards([raw1, raw2, jpeg1, jpeg2])

    assert selection.raw_card == raw1
    assert selection.jpeg_card == jpeg1
    assert selection.warnings == [
        "Multiple RAW cards found; using /media/raw1",
        "Multiple JPEG cards found; using /media/jpeg1",
    ]
