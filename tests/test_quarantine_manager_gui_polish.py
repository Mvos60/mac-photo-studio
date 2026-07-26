from pathlib import Path
from types import SimpleNamespace

from mps.gui.quarantine_manager import (
    item_detail_values,
    item_status,
    photo_library_for_import_root,
    quarantine_folder_for_import_root,
)


def make_item(restorable: bool) -> SimpleNamespace:
    return SimpleNamespace(
        stem="DSC0001",
        restorable=restorable,
        original_raw_path=Path("/library/2026/07/session/DSC0001.ARW"),
        raw_quarantine_path=Path(
            "/library/2026/07/session/.mps_quarantine/"
            "culling/DSC0001/DSC0001.ARW"
        ),
        quarantine_root=Path(
            "/library/2026/07/session/.mps_quarantine/"
            "culling/DSC0001"
        ),
    )


def test_item_status_ready_to_restore() -> None:
    assert (
        item_status(make_item(True))
        == "Ready to restore"
    )


def test_item_status_incomplete() -> None:
    assert (
        item_status(make_item(False))
        == "Incomplete"
    )


def test_photo_library_for_calendar_import_root() -> None:
    import_root = Path("/home/mac/Pictures/2026/07/15_Test")
    assert photo_library_for_import_root(import_root) == Path(
        "/home/mac/Pictures"
    )


def test_quarantine_folder_for_import_root() -> None:
    import_root = Path("/home/mac/Pictures/2026/07/15_Test")
    assert quarantine_folder_for_import_root(import_root) == (
        import_root / ".mps_quarantine" / "culling"
    )


def test_item_detail_values_selected_item() -> None:
    item = make_item(True)
    assert item_detail_values(item) == (
        "DSC0001",
        str(item.original_raw_path),
        str(item.raw_quarantine_path),
    )


def test_item_detail_values_no_selection() -> None:
    assert item_detail_values(None) == (
        "No photograph selected",
        "—",
        "—",
    )

