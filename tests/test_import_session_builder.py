from pathlib import Path

from mps.services.import_session_builder import build_import_session


def test_build_import_session():
    session = build_import_session(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder="~/raw",
        jpeg_folder="~/jpg",
    )

    assert session.year == 2026
    assert session.project == "Adriatic"
    assert session.day == "03_Slovenia"

    assert session.raw_folder == Path("~/raw").expanduser()
    assert session.jpeg_folder == Path("~/jpg").expanduser()
