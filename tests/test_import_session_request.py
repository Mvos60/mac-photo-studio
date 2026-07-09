from pathlib import Path

from mps.models.import_session_request import ImportSessionRequest


def test_import_session_request():
    request = ImportSessionRequest(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=Path("/raw"),
        jpeg_folder=Path("/jpg"),
    )

    assert request.year == 2026
    assert request.project == "Adriatic"
    assert request.day == "03_Slovenia"
    assert request.raw_folder == Path("/raw")
    assert request.jpeg_folder == Path("/jpg")
