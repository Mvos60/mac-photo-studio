from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_inventory import ImportMediaKind
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.import_media_inventory import classify_import_media


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


def test_classify_empty_media():
    inventory = classify_import_media(
        ImportMediaSelection(sources=[])
    )

    assert inventory.kind == ImportMediaKind.EMPTY
    assert inventory.complete_pair_inventory is False


def test_classify_raw_only_media():
    inventory = classify_import_media(
        ImportMediaSelection(
            sources=[
                _card("/media/raw", raw=500),
            ]
        )
    )

    assert inventory.kind == ImportMediaKind.RAW_ONLY
    assert inventory.complete_pair_inventory is False


def test_classify_jpeg_only_media():
    inventory = classify_import_media(
        ImportMediaSelection(
            sources=[
                _card("/media/jpeg", jpeg=500),
            ]
        )
    )

    assert inventory.kind == ImportMediaKind.JPEG_ONLY
    assert inventory.complete_pair_inventory is False


def test_classify_raw_and_jpeg_media():
    inventory = classify_import_media(
        ImportMediaSelection(
            sources=[
                _card("/media/raw", raw=500),
                _card("/media/jpeg", jpeg=500),
            ]
        )
    )

    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is True


def test_mixed_card_can_be_complete_pair_inventory():
    inventory = classify_import_media(
        ImportMediaSelection(
            sources=[
                _card(
                    "/media/mixed",
                    raw=500,
                    jpeg=500,
                ),
            ]
        )
    )

    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is True


def test_raw_and_jpeg_counts_can_be_unbalanced():
    inventory = classify_import_media(
        ImportMediaSelection(
            sources=[
                _card("/media/raw", raw=500),
                _card("/media/jpeg", jpeg=450),
            ]
        )
    )

    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is False
