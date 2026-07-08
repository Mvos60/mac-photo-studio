from pathlib import Path

from mps.models.import_decision import ImportDecision
from mps.config import Settings
from mps.services.import_planner import create_import_decision, create_import_plan


def test_import_decision():
    decision = ImportDecision(
        destination=Path("/tmp/photos"),
        total_files=10,
        estimated_size_bytes=12345,
        warnings=["Example warning"],
    )

    assert decision.destination == Path("/tmp/photos")
    assert decision.total_files == 10
    assert decision.estimated_size_bytes == 12345
    assert decision.warnings == ["Example warning"]
    
    from mps.config import Settings
from mps.services.import_planner import (
    create_import_decision,
    create_import_plan,
)


def test_create_import_decision(tmp_path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")

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
