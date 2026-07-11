from pathlib import Path

from mps.config import Settings
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_request_planner import create_plan_from_request


def test_create_plan_from_request(tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpeg / "DSC0001.JPG").write_bytes(b"jpeg")

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

    request = ImportSessionRequest(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpeg,
    )

    plan = create_plan_from_request(request, settings)

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
