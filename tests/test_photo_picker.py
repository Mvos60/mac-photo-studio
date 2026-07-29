from pathlib import Path

from mps.gui.photo_picker import (
    is_supported_photo,
    visible_photo_entries,
)


def test_is_supported_photo_accepts_raw_and_jpeg(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "DSC0001.ARW"
    jpeg = tmp_path / "DSC0001.JPG"
    raw.write_bytes(b"raw")
    jpeg.write_bytes(b"jpeg")

    assert is_supported_photo(raw)
    assert is_supported_photo(jpeg)


def test_is_supported_photo_rejects_unsupported_file(
    tmp_path: Path,
) -> None:
    text = tmp_path / "notes.txt"
    text.write_text("notes", encoding="utf-8")

    assert not is_supported_photo(text)


def test_visible_photo_entries_sorts_folders_before_photos(
    tmp_path: Path,
) -> None:
    (tmp_path / "Zulu").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "B.JPG").write_bytes(b"jpeg")
    (tmp_path / "a.ARW").write_bytes(b"raw")

    result = visible_photo_entries(tmp_path)

    assert [path.name for path in result] == [
        "alpha",
        "Zulu",
        "a.ARW",
        "B.JPG",
    ]


def test_visible_photo_entries_hides_dot_and_system_folders(
    tmp_path: Path,
) -> None:
    (tmp_path / ".Trash-1000").mkdir()
    (tmp_path / "lost+found").mkdir()
    (tmp_path / "Visible").mkdir()

    result = visible_photo_entries(tmp_path)

    assert [path.name for path in result] == ["Visible"]


def test_visible_photo_entries_keeps_mps_originals_accessible(
    tmp_path: Path,
) -> None:
    (tmp_path / "01_ORIGINALS").mkdir()

    result = visible_photo_entries(tmp_path)

    assert [path.name for path in result] == ["01_ORIGINALS"]


def test_visible_photo_entries_ignores_non_photo_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "photo.PNG").write_bytes(b"png")
    (tmp_path / "manifest.json").write_text(
        "{}",
        encoding="utf-8",
    )

    result = visible_photo_entries(tmp_path)

    assert [path.name for path in result] == ["photo.PNG"]


def test_visible_photo_entries_returns_empty_for_missing_folder(
    tmp_path: Path,
) -> None:
    result = visible_photo_entries(tmp_path / "missing")

    assert result == []


def test_photo_picker_supports_task_specific_text() -> None:
    source = Path(
        "mps/gui/photo_picker.py"
    ).read_text(encoding="utf-8")

    assert "description: str" in source
    assert "text=self._title" in source
    assert "text=self._description" in source


def test_gui_app_explains_photo_picker_purpose() -> None:
    source = Path(
        "mps/gui/app.py"
    ).read_text(encoding="utf-8")

    assert "Select the photograph you want MPS to verify." in source
    assert "Select the photograph whose MPS provenance history " in source
    assert "you want to view." in source
