from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_inventory import ImportMediaKind
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_session import add_media_to_session


def _card(
    root: Path,
    *,
    raw: int = 0,
    jpeg: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
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


def _write_photo(
    root: Path,
    name: str,
    content: bytes,
) -> None:
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True, exist_ok=True)
    (dcim / name).write_bytes(content)


def test_new_media_session_is_empty():
    session = ImportMediaSession()

    assert session.sources == []
    assert session.source_fingerprints == set()
    assert session.processed_source_files == []
    assert session.selection.empty is True


def test_add_single_raw_card_to_session(tmp_path: Path):
    root = tmp_path / "raw"
    _write_photo(root, "DSC0001.ARW", b"raw")

    session = ImportMediaSession()

    inventory = add_media_to_session(
        session,
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
    )

    assert len(session.sources) == 1
    assert len(session.source_fingerprints) == 1
    assert inventory.kind == ImportMediaKind.RAW_ONLY
    assert inventory.selection.total_raw_files == 1


def test_sequential_cards_can_use_same_mount_path(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw")

    session = ImportMediaSession()

    first_inventory = add_media_to_session(
        session,
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
    )

    raw_file = root / "DCIM" / "100MSDCF" / "DSC0001.ARW"
    raw_file.unlink()

    _write_photo(root, "DSC0001.JPG", b"jpeg")

    second_inventory = add_media_to_session(
        session,
        ImportMediaSelection(
            sources=[
                _card(root, jpeg=1),
            ]
        ),
    )

    assert first_inventory.kind == ImportMediaKind.RAW_ONLY
    assert second_inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert second_inventory.selection.total_raw_files == 1
    assert second_inventory.selection.total_jpeg_files == 1
    assert second_inventory.selection.source_count == 2
    assert len(session.source_fingerprints) == 2


def test_simultaneous_raw_and_jpeg_cards_are_combined(
    tmp_path: Path,
):
    raw_root = tmp_path / "raw"
    jpeg_root = tmp_path / "jpeg"

    _write_photo(raw_root, "DSC0001.ARW", b"raw")
    _write_photo(jpeg_root, "DSC0001.JPG", b"jpeg")

    session = ImportMediaSession()

    inventory = add_media_to_session(
        session,
        ImportMediaSelection(
            sources=[
                _card(raw_root, raw=1),
                _card(jpeg_root, jpeg=1),
            ]
        ),
    )

    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is True
    assert inventory.selection.source_count == 2


def test_mixed_card_is_valid_session_media(tmp_path: Path):
    root = tmp_path / "mixed"

    _write_photo(root, "DSC0001.ARW", b"raw")
    _write_photo(root, "DSC0001.JPG", b"jpeg")

    session = ImportMediaSession()

    inventory = add_media_to_session(
        session,
        ImportMediaSelection(
            sources=[
                _card(
                    root,
                    raw=1,
                    jpeg=1,
                ),
            ]
        ),
    )

    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is True
    assert inventory.selection.source_count == 1


def test_same_media_is_not_added_twice(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw")

    session = ImportMediaSession()
    selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    add_media_to_session(session, selection)
    add_media_to_session(session, selection)

    assert len(session.sources) == 1
    assert len(session.source_fingerprints) == 1
    assert session.selection.total_raw_files == 1


def test_many_sequential_sources_are_accumulated(
    tmp_path: Path,
):
    session = ImportMediaSession()

    sources = [
        ("raw1", "DSC0001.ARW", b"raw1", 1, 0),
        ("raw2", "DSC0002.ARW", b"raw2", 1, 0),
        ("jpeg1", "DSC0001.JPG", b"jpeg1", 0, 1),
        ("jpeg2", "DSC0002.JPG", b"jpeg2", 0, 1),
    ]

    for directory, filename, content, raw, jpeg in sources:
        root = tmp_path / directory
        _write_photo(root, filename, content)

        inventory = add_media_to_session(
            session,
            ImportMediaSelection(
                sources=[
                    _card(
                        root,
                        raw=raw,
                        jpeg=jpeg,
                    )
                ]
            ),
        )

    assert inventory.selection.source_count == 4
    assert inventory.selection.total_raw_files == 2
    assert inventory.selection.total_jpeg_files == 2
    assert inventory.kind == ImportMediaKind.RAW_AND_JPEG
    assert inventory.complete_pair_inventory is True
    assert len(session.source_fingerprints) == 4


def test_processed_source_files_are_accumulated_without_duplicates():
    session = ImportMediaSession()

    raw = Path("/media/card/DCIM/DSC0001.ARW")
    jpeg = Path("/media/card/DCIM/DSC0001.JPG")

    first_added = session.add_processed_source_files(
        [raw]
    )
    second_added = session.add_processed_source_files(
        [raw, jpeg]
    )

    assert first_added == 1
    assert second_added == 1
    assert session.processed_source_files == [
        raw,
        jpeg,
    ]
