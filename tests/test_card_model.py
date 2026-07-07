from pathlib import Path

from mps.models.card import CardScanResult


def test_card_scan_result_has_photos():
    result = CardScanResult(
        root=Path("/tmp/card"),
        dcim_path=None,
        raw_count=1,
        jpeg_count=0,
        heif_count=0,
        video_count=0,
        pair_count=0,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=10,
    )

    assert result.has_photos


def test_card_scan_result_to_dict():
    result = CardScanResult(
        root=Path("/tmp/card"),
        dcim_path=Path("/tmp/card/DCIM"),
        raw_count=2,
        jpeg_count=2,
        heif_count=1,
        video_count=1,
        pair_count=2,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=3,
        total_size_bytes=12345,
    )

    data = result.to_dict()

    assert data["root"] == "/tmp/card"
    assert data["dcim_path"] == "/tmp/card/DCIM"
    assert data["pair_count"] == 2
    assert data["video_count"] == 1
    assert data["total_size_bytes"] == 12345
