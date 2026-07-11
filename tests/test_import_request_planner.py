from pathlib import Path

from mps.config import Settings
from mps.models.import_decision import CopyOperation
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_request_planner import (
    create_decision_from_request,
    create_plan_from_request,
)


def settings(tmp_path: Path) -> Settings:
    return Settings(
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


def request(raw: Path, jpeg: Path) -> ImportSessionRequest:
    return ImportSessionRequest(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpeg,
    )


def test_create_plan_from_request(tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpeg / "DSC0001.JPG").write_bytes(b"jpeg")

    plan = create_plan_from_request(
        request(raw, jpeg),
        settings(tmp_path),
    )

    assert plan.year == 2026
    assert plan.project == "Adriatic"
    assert plan.day == "03_Slovenia"
    assert plan.raw_folder == raw
    assert plan.jpeg_folder == jpeg
    assert plan.destination == (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )
    assert plan.pairing.pair_count == 1
    assert plan.total_source_files == 2
    assert not plan.destination.exists()


def test_create_decision_from_request(tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    raw_file = raw / "DSC0001.ARW"
    jpeg_file = jpeg / "DSC0001.JPG"

    raw_file.write_bytes(b"raw")
    jpeg_file.write_bytes(b"jpeg")

    plan, decision = create_decision_from_request(
        request(raw, jpeg),
        settings(tmp_path),
    )

    assert decision.destination == plan.destination
    assert decision.total_files == 2
    assert decision.estimated_size_bytes == 7
    assert decision.warnings == []

    assert CopyOperation(
        source=raw_file,
        destination=plan.destination / "DSC0001.ARW",
    ) in decision.copy_operations

    assert CopyOperation(
        source=jpeg_file,
        destination=plan.destination / "DSC0001.JPG",
    ) in decision.copy_operations

    assert not decision.destination.exists()
