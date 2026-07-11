from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection


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


def test_empty_media_selection():
    selection = ImportMediaSelection(sources=[])

    assert selection.source_count == 0
    assert selection.total_raw_files == 0
    assert selection.total_jpeg_files == 0
    assert selection.has_raw is False
    assert selection.has_jpeg is False
    assert selection.empty is True


def test_single_raw_only_source():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/card", raw=500),
        ]
    )

    assert selection.source_count == 1
    assert selection.total_raw_files == 500
    assert selection.total_jpeg_files == 0
    assert selection.has_raw is True
    assert selection.has_jpeg is False
    assert selection.empty is False


def test_single_raw_and_jpeg_source():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/card", raw=500, jpeg=500),
        ]
    )

    assert selection.source_count == 1
    assert selection.total_raw_files == 500
    assert selection.total_jpeg_files == 500
    assert selection.has_raw is True
    assert selection.has_jpeg is True


def test_multiple_sources_are_combined():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/raw", raw=500),
            _card("/media/jpeg", jpeg=500),
        ]
    )

    assert selection.source_count == 2
    assert selection.total_raw_files == 500
    assert selection.total_jpeg_files == 500
    assert selection.has_raw is True
    assert selection.has_jpeg is True


def test_many_sources_are_combined():
    selection = ImportMediaSelection(
        sources=[
            _card("/media/raw1", raw=300),
            _card("/media/raw2", raw=200),
            _card("/media/jpeg1", jpeg=250),
            _card("/media/jpeg2", jpeg=250),
        ]
    )

    assert selection.source_count == 4
    assert selection.total_raw_files == 500
    assert selection.total_jpeg_files == 500
