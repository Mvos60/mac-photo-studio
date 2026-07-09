from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.import_card_discovery import discover_import_cards


def test_discover_import_cards(monkeypatch):
    settings = Settings({})

    card = CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
        raw_count=25,
        jpeg_count=25,
        heif_count=0,
        video_count=0,
        pair_count=25,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=1234,
    )

    monkeypatch.setattr(
        "mps.services.import_card_discovery.scan_cards",
        lambda settings: [card],
    )

    result = discover_import_cards(settings)

    assert result.raw_card == card
    assert result.jpeg_card == card
    assert result.warnings == []
