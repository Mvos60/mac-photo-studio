from pathlib import Path

from mps.models.card import CardScanResult
from mps.services.import_media_selector import select_import_media


def _card(
    root: str,
    *,
    raw: int = 0,
    jpeg: int = 0,
    video: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=Path(root),
        dcim_path=Path(root) / "DCIM",
        raw_count=raw,
        jpeg_count=jpeg,
        heif_count=0,
        video_count=video,
        pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0),
        other_count=0,
        total_size_bytes=0,
    )


def test_select_import_media_keeps_raw_only_card():
    card = _card("/media/raw", raw=500)

    selection = select_import_media([card])

    assert selection.sources == [card]


def test_select_import_media_keeps_mixed_card():
    card = _card(
        "/media/mixed",
        raw=500,
        jpeg=500,
    )

    selection = select_import_media([card])

    assert selection.sources == [card]


def test_select_import_media_keeps_multiple_photo_cards():
    raw = _card("/media/raw", raw=500)
    jpeg = _card("/media/jpeg", jpeg=500)

    selection = select_import_media([raw, jpeg])

    assert selection.sources == [raw, jpeg]
    assert selection.source_count == 2


def test_select_import_media_does_not_choose_first_candidate():
    raw1 = _card("/media/raw1", raw=300)
    raw2 = _card("/media/raw2", raw=200)
    jpeg1 = _card("/media/jpeg1", jpeg=250)
    jpeg2 = _card("/media/jpeg2", jpeg=250)

    selection = select_import_media(
        [raw1, raw2, jpeg1, jpeg2]
    )

    assert selection.sources == [
        raw1,
        raw2,
        jpeg1,
        jpeg2,
    ]
    assert selection.source_count == 4


def test_select_import_media_ignores_non_photo_media():
    video = _card("/media/video", video=10)

    selection = select_import_media([video])

    assert selection.sources == []
    assert selection.empty is True
