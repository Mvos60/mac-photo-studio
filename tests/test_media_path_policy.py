from pathlib import Path

from mps.services.media_path_policy import (
    is_excluded_media_directory_name,
    is_excluded_media_path,
    media_files,
)


def test_trash_directory_names_are_excluded():
    assert is_excluded_media_directory_name(
        ".Trash-1000"
    )
    assert is_excluded_media_directory_name(
        ".Trashes"
    )
    assert is_excluded_media_directory_name(
        ".TRASH"
    )


def test_removable_media_system_directories_are_excluded():
    assert is_excluded_media_directory_name(
        "$RECYCLE.BIN"
    )
    assert is_excluded_media_directory_name(
        "System Volume Information"
    )


def test_normal_camera_directory_is_not_excluded():
    assert not is_excluded_media_directory_name(
        "100MSDCF"
    )


def test_photo_below_trash_directory_is_excluded(
    tmp_path: Path,
):
    root = tmp_path / "card"

    photo = (
        root
        / "DCIM"
        / ".Trash-1000"
        / "files"
        / "DSC0001.ARW"
    )

    assert is_excluded_media_path(
        photo,
        root / "DCIM",
    )


def test_normal_photo_path_is_not_excluded(
    tmp_path: Path,
):
    root = tmp_path / "card"

    photo = (
        root
        / "DCIM"
        / "100MSDCF"
        / "DSC0001.ARW"
    )

    assert not is_excluded_media_path(
        photo,
        root / "DCIM",
    )


def test_media_files_ignores_trash_and_system_directories(
    tmp_path: Path,
):
    root = tmp_path / "card"

    normal = (
        root
        / "DCIM"
        / "100MSDCF"
        / "DSC0001.ARW"
    )
    trash = (
        root
        / "DCIM"
        / ".Trash-1000"
        / "files"
        / "DSC0002.ARW"
    )
    recycled = (
        root
        / "DCIM"
        / "$RECYCLE.BIN"
        / "DSC0003.JPG"
    )
    system = (
        root
        / "DCIM"
        / "System Volume Information"
        / "DSC0004.JPG"
    )

    for path in (
        normal,
        trash,
        recycled,
        system,
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(b"photo")

    assert media_files(root / "DCIM") == [
        normal
    ]
