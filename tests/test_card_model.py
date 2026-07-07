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
