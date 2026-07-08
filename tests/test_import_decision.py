from pathlib import Path

from mps.config import Settings
from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_planner import create_import_decision, create_import_plan


def test_import_decision():
    operation = CopyOperation(
        source=Path("/tmp/raw/DSC0001.ARW"),
        destination=Path("/tmp/photos/DSC0001.ARW"),
    )

    decision = ImportDecision(
        destination=Path("/tmp/photos"),
        total_files=1,
        estimated_size_bytes=12345,
        copy_operations=[operation],
        warnings=["Example warning"],
    )

    assert decision.destination == Path("/tmp/photos")
    assert decision.total_files == 1
    assert decision.estimated_size_bytes == 12345
    assert decision.copy_operations == [operation]
    assert decision.warnings == ["Example warning"]


def test_create_import_decision(tmp_path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    raw_file = raw / "DSC0001.ARW"
    jpg_file = jpg / "DSC0001.JPG"

    raw_file.write_bytes(b"raw")
    jpg_file.write_bytes(b"jpg")

    settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )

    plan = create_import_plan(
        project="Adriatic_2026",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpg,
        settings=settings,
    )

    decision = create_import_decision(plan)

    assert decision.destination == plan.destination
    assert decision.total_files == plan.total_source_files
    assert decision.estimated_size_bytes == plan.estimated_size_bytes
    assert decision.warnings == []

    assert len(decision.copy_operations) == 2
    assert CopyOperation(
        source=raw_file,
        destination=plan.destination / "DSC0001.ARW",
    ) in decision.copy_operations
    assert CopyOperation(
        source=jpg_file,
        destination=plan.destination / "DSC0001.JPG",
    ) in decision.copy_operations
