from pathlib import Path
from types import SimpleNamespace

import pytest

from mps.gui import quarantine_manager as quarantine_manager_module
from mps.gui.quarantine_manager import (
    item_detail_values,
    item_status,
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


@pytest.mark.parametrize(
    "relative_import_root",
    [
        Path("2026/Adriatic/03_Slovenia"),
        Path("2026/08/01_Ljubljana/Adriatic"),
    ],
)
def test_show_quarantine_manager_uses_configured_photo_library(
    relative_import_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    photo_library = tmp_path / "Photos_Master"
    import_root = photo_library / relative_import_root
    library_calls = []
    picker_calls = []
    dialog_calls = []

    monkeypatch.setattr(
        quarantine_manager_module,
        "get_photo_library",
        lambda: library_calls.append(None) or photo_library,
    )
    monkeypatch.setattr(
        quarantine_manager_module,
        "choose_import_session",
        lambda **kwargs: picker_calls.append(kwargs) or import_root,
    )
    monkeypatch.setattr(
        quarantine_manager_module,
        "QuarantineManagerDialog",
        lambda **kwargs: dialog_calls.append(kwargs),
    )

    parent = object()
    quarantine_manager_module.show_quarantine_manager(parent)

    assert library_calls == [None]
    assert picker_calls == [
        {
            "parent": parent,
            "photo_library": photo_library,
            "title": "Choose the photo shoot to review",
        }
    ]
    assert dialog_calls == [
        {
            "parent": parent,
            "import_root": import_root,
            "photo_library": photo_library,
        }
    ]


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


def test_quarantine_manager_uses_title_case_for_section_and_dialog_titles() -> None:
    source = Path(
        "mps/gui/quarantine_manager.py"
    ).read_text(encoding="utf-8")

    expected = (
        'text="What Can I Do Here?"',
        'text="Selected Photograph Details"',
        'text="Recovery Status"',
        'dialog.title(f"Quarantine Details — {item.stem}")',
        '"Restore Unavailable"',
        '"Confirm Restore"',
        '"Restore Report"',
        '"Permanent Removal"',
        '"Permanent Removal Cancelled"',
        '"Permanent Removal Report"',
        'dialog.title("Confirm Permanent Removal")',
    )
    legacy = (
        'text="What can I do here?"',
        'text="Selected photograph details"',
        'text="Recovery status"',
        'dialog.title(f"Quarantine details — {item.stem}")',
        '"Restore unavailable"',
        '"Confirm restore"',
        '"Restore report"',
        '"Permanent removal"',
        '"Permanent removal cancelled"',
        '"Permanent removal report"',
        'dialog.title("Confirm permanent removal")',
    )

    for value in expected:
        assert value in source

    for value in legacy:
        assert value not in source
