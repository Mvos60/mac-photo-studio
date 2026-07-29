from pathlib import Path

from mps.gui.session_picker import (
    has_culling_content,
    visible_directories,
)


def test_visible_directories_returns_sorted_folders(
    tmp_path: Path,
):
    (tmp_path / "Zulu").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "Bravo").mkdir()
    (tmp_path / "photo.jpg").write_bytes(b"jpg")

    result = visible_directories(tmp_path)

    assert [path.name for path in result] == [
        "alpha",
        "Bravo",
        "Zulu",
    ]


def test_visible_directories_hides_dot_directories(
    tmp_path: Path,
):
    (tmp_path / ".Trash-1000").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "Visible").mkdir()

    result = visible_directories(tmp_path)

    assert [path.name for path in result] == [
        "Visible",
    ]


def test_visible_directories_hides_mps_internal_folders(
    tmp_path: Path,
):
    (tmp_path / "01_ORIGINALS").mkdir()
    (tmp_path / "02_WORKING").mkdir()
    (tmp_path / "99_ADMIN").mkdir()
    (tmp_path / "provenance").mkdir()
    (tmp_path / "Session").mkdir()

    result = visible_directories(tmp_path)

    assert [path.name for path in result] == [
        "Session",
    ]


def test_visible_directories_returns_empty_for_missing_folder(
    tmp_path: Path,
):
    result = visible_directories(
        tmp_path / "missing"
    )

    assert result == []


def test_has_culling_content_accepts_mps_originals_folder(
    tmp_path: Path,
):
    session = tmp_path / "Session"
    session.mkdir()
    (session / "01_ORIGINALS").mkdir()

    assert has_culling_content(session)


def test_has_culling_content_accepts_raw_photo(
    tmp_path: Path,
):
    session = tmp_path / "Session"
    session.mkdir()
    (session / "MAC00001.ARW").write_bytes(b"raw")

    assert has_culling_content(session)


def test_has_culling_content_accepts_jpeg_photo(
    tmp_path: Path,
):
    session = tmp_path / "Session"
    session.mkdir()
    (session / "MAC00001.JPG").write_bytes(b"jpeg")

    assert has_culling_content(session)


def test_has_culling_content_rejects_project_container(
    tmp_path: Path,
):
    project = tmp_path / "Project"
    project.mkdir()
    (project / "Session").mkdir()

    assert not has_culling_content(project)


def test_has_culling_content_rejects_missing_folder(
    tmp_path: Path,
):
    assert not has_culling_content(
        tmp_path / "missing"
    )
