import hashlib
import json
from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_file_result import (
    ImportFileMediaType,
    ImportFileResultStatus,
)
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


def test_explicit_source_subset_plans_only_selected_files(tmp_path: Path):
    root = tmp_path / "mixed"
    selected_raw = _write_photo(root, "DSC0001.ARW", b"raw-one")
    selected_jpg = _write_photo(root, "DSC0001.JPG", b"jpg-one")
    _write_photo(root, "DSC0002.ARW", b"raw-two")
    _write_photo(root, "DSC0002.JPG", b"jpg-two")

    plan = create_media_batch_plan(
        ImportMediaSelection(sources=[_card(root, raw=2, jpeg=2)]),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        source_files=(selected_raw, selected_jpg),
    )

    assert {operation.source for operation in plan.decision.copy_operations} == {
        selected_raw, selected_jpg,
    }


def test_explicit_source_subset_still_applies_duplicate_registry(tmp_path: Path):
    root = tmp_path / "mixed"
    duplicate = _write_photo(root, "DSC0001.ARW", b"already-imported")
    selected = _write_photo(root, "DSC0002.ARW", b"new")
    _write_imported_hash(tmp_path / "Photos_Master", b"already-imported")

    plan = create_media_batch_plan(
        ImportMediaSelection(sources=[_card(root, raw=2)]),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        source_files=(duplicate, selected),
    )

    assert [operation.source for operation in plan.decision.copy_operations] == [
        selected,
    ]


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


def test_previously_imported_file_reports_one_typed_skip(tmp_path: Path):
    photos_root = tmp_path / "Photos_Master"
    root = tmp_path / "card"
    _write_imported_hash(photos_root, b"already-imported")
    source = _write_photo(root, "DSC0001.ARW", b"already-imported")
    results = []

    plan = create_media_batch_plan(
        ImportMediaSelection(sources=[_card(root, raw=1)]),
        _settings(tmp_path),
        year=2026,
        project="NewProject",
        day="NewSession",
        file_result_callback=results.append,
    )

    assert plan.total_files == 0
    assert len(results) == 1
    assert results[0].source == source
    assert results[0].destination is None
    assert results[0].media_type is ImportFileMediaType.RAW
    assert results[0].status is ImportFileResultStatus.SKIPPED
    assert results[0].reason_code == "already_imported"


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

def test_quarantined_previously_imported_file_is_not_planned(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    card_root = tmp_path / "card"
    content = b"quarantined-photo"

    import_root = (
        photos_root
        / "2026"
        / "Existing"
        / "Session"
    )
    quarantine = (
        import_root
        / ".mps_quarantine"
        / "culling"
        / "DSC0001"
    )
    quarantine.mkdir(parents=True)

    known_hash = hashlib.sha256(
        content
    ).hexdigest()

    snapshot = {
        "entries": [
            {
                "camera_model": "ILCE-7M3",
                "certificate_id": "MPS-CERT-1",
                "certificate_path": (
                    "/photos/provenance/MPS-CERT-1.json"
                ),
                "created_at": "2026-07-15T08:00:00+00:00",
                "destination_path": (
                    "/photos/2026/Existing/Session/DSC0001.ARW"
                ),
                "provenance_id": "MPS-PROV-1",
                "session_id": "MPS-SESSION-1",
                "sha256": known_hash,
            }
        ]
    }

    (
        quarantine
        / "certificate_index.before.json"
    ).write_text(
        json.dumps(snapshot),
        encoding="utf-8",
    )

    _write_photo(
        card_root,
        "DSC0001.ARW",
        content,
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[
                _card(card_root, raw=1),
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

def test_planner_reports_duplicate_checking_progress(
    tmp_path: Path,
):
    root = tmp_path / "card"

    _write_photo(
        root,
        "DSC0001.ARW",
        b"raw-photo",
    )
    _write_photo(
        root,
        "DSC0001.JPG",
        b"jpeg-photo",
    )

    seen = []

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
        project="Progress",
        day="Session",
        progress_callback=seen.append,
    )

    assert plan.total_files == 2
    assert [
        progress.phase
        for progress in seen
    ] == ["checking"] * 4
    assert [
        (
            progress.current,
            progress.total,
            progress.percent,
        )
        for progress in seen
    ] == [
        (0, 2, 0),
        (1, 2, 50),
        (1, 2, 50),
        (2, 2, 100),
    ]

def test_calendar_destination_selection_is_authoritative(
    tmp_path: Path,
):
    card_root = tmp_path / "card"
    _write_photo(card_root, "DSC0001.ARW", b"raw")
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(
            sources=[_card(card_root, raw=1)]
        ),
        _settings(tmp_path),
        year=1999,
        project="Legacy Project",
        day="Legacy Day",
        destination_selection=destination_selection,
    )

    assert plan.destination == (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )
    assert plan.destination.exists() is False


def test_calendar_destination_without_description(
    tmp_path: Path,
):
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(sources=[]),
        _settings(tmp_path),
        year=1999,
        project="Legacy Project",
        day="Legacy Day",
        destination_selection=destination_selection,
    )

    assert plan.destination == (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "08"
        / "01"
        / "Adriatic"
    )
    assert plan.destination.exists() is False


def test_calendar_destination_respects_alternate_photos_root(
    tmp_path: Path,
):
    alternate_root = tmp_path / "Alternate Library"
    settings = Settings(
        {
            "paths": {
                "photos_root": str(alternate_root),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )

    plan = create_media_batch_plan(
        ImportMediaSelection(sources=[]),
        settings,
        year=1999,
        project="Legacy Project",
        day="Legacy Day",
        destination_selection=destination_selection,
    )

    assert plan.destination == (
        alternate_root
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )
    assert alternate_root.exists() is False


def test_explicit_source_subset_rejects_path_outside_discovered_media(
    tmp_path: Path,
):
    import pytest

    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"card")
    outside = _write_photo(tmp_path / "outside", "OTHER.ARW", b"outside")

    with pytest.raises(ValueError, match="discovered media"):
        create_media_batch_plan(
            ImportMediaSelection(sources=[_card(root, raw=1)]),
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="03_Slovenia",
            source_files=(outside,),
        )
