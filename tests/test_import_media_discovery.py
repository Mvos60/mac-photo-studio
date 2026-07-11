from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.import_media_discovery import discover_import_media


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


def test_discover_import_media_returns_single_source(monkeypatch):
    settings = Settings({})
    card = _card(
        "/media/card",
        raw=25,
        jpeg=25,
    )

    monkeypatch.setattr(
        "mps.services.import_media_discovery.scan_cards",
        lambda settings: [card],
    )

    result = discover_import_media(settings)

    assert result.sources == [card]
    assert result.source_count == 1
    assert result.total_raw_files == 25
    assert result.total_jpeg_files == 25


def test_discover_import_media_returns_all_photo_sources(monkeypatch):
    settings = Settings({})

    raw1 = _card("/media/raw1", raw=300)
    raw2 = _card("/media/raw2", raw=200)
    jpeg = _card("/media/jpeg", jpeg=500)

    monkeypatch.setattr(
        "mps.services.import_media_discovery.scan_cards",
        lambda settings: [
            raw1,
            raw2,
            jpeg,
        ],
    )

    result = discover_import_media(settings)

    assert result.sources == [
        raw1,
        raw2,
        jpeg,
    ]
    assert result.source_count == 3
    assert result.total_raw_files == 500
    assert result.total_jpeg_files == 500


def test_discover_import_media_can_be_empty(monkeypatch):
    settings = Settings({})

    monkeypatch.setattr(
        "mps.services.import_media_discovery.scan_cards",
        lambda settings: [],
    )

    result = discover_import_media(settings)

    assert result.sources == []
    assert result.empty is True
