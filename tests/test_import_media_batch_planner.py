import hashlib
import json
from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.import_media_batch_planner import (
    create_media_batch_plan,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


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
) -> Path:
    directory = root / "DCIM" / "100MSDCF"
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / name
    path.write_bytes(content)

    return path


def _write_imported_hash(
    photos_root: Path,
    content: bytes,
) -> None:
    import_root = (
        photos_root
        / "2026"
        / "Existing"
        / "Session"
    )
    provenance = import_root / "provenance"
    provenance.mkdir(parents=True, exist_ok=True)

    known_hash = hashlib.sha256(
        content
    ).hexdigest()

    data = {
        "entries": [
            {
                "camera_model": "ILCE-7M3",
                "certificate_id": "MPS-CERT-1",
                "certificate_path": (
                    str(
                        provenance
                        / "MPS-CERT-1.json"
                    )
                ),
                "created_at": "2026-07-15T08:00:00+00:00",
                "destination_path": str(
                    import_root / "DSC0001.ARW"
                ),
                "provenance_id": "MPS-PROV-1",
                "session_id": "MPS-SESSION-1",
                "sha256": known_hash,
            }
        ]
    }

    (
        provenance / "certificate_index.json"
    ).write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def test_plan_single_raw_card(tmp_path: Path):
    root = tmp_path / "raw"
    raw_file = _write_photo(
        root,
        "DSC0001.ARW",
        b"raw",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 1
    assert plan.estimated_size_bytes == 3
    assert plan.destination == (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )
    assert plan.decision.copy_operations[0].source == raw_file
    assert plan.decision.copy_operations[0].destination == (
        plan.destination / "DSC0001.ARW"
    )
    assert plan.decision.warnings == []


def test_plan_mixed_raw_and_jpeg_card(tmp_path: Path):
    root = tmp_path / "mixed"

    _write_photo(root, "DSC0001.ARW", b"raw")
    _write_photo(root, "DSC0001.JPG", b"jpeg")

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(
                    root,
                    raw=1,
                    jpeg=1,
                ),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 2
    assert {
        operation.source.name
        for operation in plan.decision.copy_operations
    } == {
        "DSC0001.ARW",
        "DSC0001.JPG",
    }


def test_plan_multiple_simultaneous_cards(tmp_path: Path):
    raw_root = tmp_path / "raw"
    jpeg_root = tmp_path / "jpeg"

    _write_photo(raw_root, "DSC0001.ARW", b"raw")
    _write_photo(jpeg_root, "DSC0001.JPG", b"jpeg")

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(raw_root, raw=1),
                _card(jpeg_root, jpeg=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 2
    assert {
        operation.source.name
        for operation in plan.decision.copy_operations
    } == {
        "DSC0001.ARW",
        "DSC0001.JPG",
    }


def test_non_photo_files_are_not_planned(tmp_path: Path):
    root = tmp_path / "card"

    _write_photo(root, "DSC0001.ARW", b"raw")
    _write_photo(root, "README.TXT", b"notes")
    _write_photo(root, "C0001.MP4", b"video")

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 1
    assert (
        plan.decision.copy_operations[0].source.name
        == "DSC0001.ARW"
    )


def test_destination_filename_collision_is_reported(
    tmp_path: Path,
):
    first_root = tmp_path / "card1"
    second_root = tmp_path / "card2"

    _write_photo(
        first_root,
        "DSC0001.ARW",
        b"first",
    )
    _write_photo(
        second_root,
        "DSC0001.ARW",
        b"second",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(first_root, raw=1),
                _card(second_root, raw=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 2
    assert plan.decision.warnings == [
        "Multiple source files map to the same destination filename"
    ]


def test_planning_is_read_only(tmp_path: Path):
    root = tmp_path / "raw"
    _write_photo(root, "DSC0001.ARW", b"raw")

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert not plan.destination.exists()


def test_previously_imported_file_is_not_planned(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    root = tmp_path / "card"

    _write_imported_hash(
        photos_root,
        b"already-imported",
    )

    _write_photo(
        root,
        "DSC0001.ARW",
        b"already-imported",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="NewProject",
        day="NewSession",
    )

    assert plan.total_files == 0
    assert plan.estimated_size_bytes == 0
    assert plan.decision.copy_operations == []
    assert plan.decision.warnings == []


def test_only_new_files_are_planned_when_card_is_reused(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    root = tmp_path / "card"

    _write_imported_hash(
        photos_root,
        b"old-photo",
    )

    _write_photo(
        root,
        "DSC0001.ARW",
        b"old-photo",
    )
    new_file = _write_photo(
        root,
        "DSC0002.ARW",
        b"new-photo",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(root, raw=2),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="NewProject",
        day="NewSession",
    )

    assert plan.total_files == 1
    assert len(plan.decision.copy_operations) == 1
    assert (
        plan.decision.copy_operations[0].source
        == new_file
    )
    assert (
        plan.decision.copy_operations[0].destination
        == plan.destination / "DSC0002.ARW"
    )


def test_trash_photo_files_are_not_planned(
    tmp_path: Path,
):
    root = tmp_path / "card"

    real_file = _write_photo(
        root,
        "DSC0001.ARW",
        b"real raw",
    )

    trash_directory = (
        root
        / "DCIM"
        / ".Trash-1000"
        / "files"
    )
    trash_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        trash_directory / "DSC0002.ARW"
    ).write_bytes(b"trash raw")

    (
        trash_directory / "DSC0002.JPG"
    ).write_bytes(b"trash jpg")

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(
                    root,
                    raw=2,
                    jpeg=1,
                ),
            ]
        ),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
    )

    assert plan.total_files == 1
    assert len(
        plan.decision.copy_operations
    ) == 1
    assert (
        plan.decision.copy_operations[0].source
        == real_file
    )
