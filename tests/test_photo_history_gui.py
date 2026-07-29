from pathlib import Path

from mps.gui.photo_history import (
    PhotoHistoryDialog,
    build_timeline_text,
    event_label,
    history_state,
    parse_history_timeline,
    readable_event_time,
    timeline_summary,
)


def _history_output() -> str:
    return """Mac Photo Studio Photo Provenance History
===========================================
Photo:         /photos/DSC0001_master.tif
Status:        TRUSTED

1. INGEST
   Time:        2026-07-01T10:00:00Z
   Application: Mac Photo Studio
   Camera:      ILCE-7M3
   Verified camera media ingest

2. EDIT
   Time:        2026-07-01T11:30:00Z
   Application: darktable 5.6.0
   RAW development
   Output:      /photos/DSC0001_master.tif
"""


def test_history_state_trusted() -> None:
    state, explanation = history_state(
        0,
        "Status:        TRUSTED\n1. INGEST",
    )

    assert state == "TRUSTED HISTORY"
    assert "valid recorded history" in explanation


def test_history_state_not_managed() -> None:
    state, explanation = history_state(
        1,
        (
            "Status:        NOT TRUSTED\n"
            "Reason:        Photo is not inside a managed "
            "provenance import"
        ),
    )

    assert state == "NOT MANAGED BY MPS"
    assert "verified MPS import" in explanation
    assert "AI-generated" in explanation


def test_history_state_changed_or_invalid() -> None:
    state, explanation = history_state(
        1,
        "Reason: Actual file SHA-256 does not match recorded identity",
    )

    assert state == "CHANGED OR INVALID HISTORY"
    assert "does not fully match" in explanation


def test_history_state_fallback() -> None:
    state, explanation = history_state(
        1,
        "Unexpected history error",
    )

    assert state == "HISTORY UNAVAILABLE"
    assert "raw history details" in explanation


def test_event_labels_are_photographer_friendly() -> None:
    assert event_label("INGEST") == "Imported"
    assert event_label("EDIT") == "Edited"
    assert event_label("DERIVATIVE") == "Derivative created"
    assert event_label("EXPORT") == "Exported"
    assert event_label("future_event") == "Future Event"


def test_readable_event_time() -> None:
    assert (
        readable_event_time("2026-07-01T10:00:00Z")
        == "2026-07-01 10:00:00 UTC"
    )
    assert readable_event_time("") == "Time not recorded"


def test_parse_history_timeline_returns_structured_events() -> None:
    entries = parse_history_timeline(
        _history_output()
    )

    assert len(entries) == 2

    ingest = entries[0]
    assert ingest.number == 1
    assert ingest.event_type == "INGEST"
    assert ingest.created_at == "2026-07-01T10:00:00Z"
    assert ingest.application == "Mac Photo Studio"
    assert ingest.camera == "ILCE-7M3"
    assert ingest.description == "Verified camera media ingest"

    edit = entries[1]
    assert edit.number == 2
    assert edit.event_type == "EDIT"
    assert edit.application == "darktable 5.6.0"
    assert edit.description == "RAW development"
    assert edit.output_path == "/photos/DSC0001_master.tif"


def test_timeline_summary_shows_journey() -> None:
    entries = parse_history_timeline(
        _history_output()
    )

    assert timeline_summary(entries) == (
        "2 recorded events\nImported  →  Edited"
    )


def test_build_timeline_text_is_readable() -> None:
    entries = parse_history_timeline(
        _history_output()
    )
    text = build_timeline_text(entries)

    assert "2 recorded events" in text
    assert "1. Imported" in text
    assert "2. Edited" in text
    assert "Camera: ILCE-7M3" in text
    assert "Details: RAW development" in text
    assert "Output: /photos/DSC0001_master.tif" in text


def test_build_timeline_text_explains_empty_history() -> None:
    text = build_timeline_text(())

    assert "No recorded provenance events" in text
    assert "Raw History Details" in text


def test_photo_history_dialog_uses_mps_framework() -> None:
    source = Path(
        "mps/gui/photo_history.py"
    ).read_text(encoding="utf-8")

    assert "MpsDialog(" in source
    assert "self._dialog.add_header(" in source
    assert "self._dialog.create_section(" in source
    assert 'title="MPS Status"' in source
    assert 'title="Photograph Journey"' in source
    assert "ttk.Notebook(" in source
    assert 'text="Readable Timeline"' in source
    assert 'text="Raw History Details"' in source
    assert "self._dialog.add_close_button()" in source
    assert "tk.Toplevel(" not in source


def test_photo_history_dialog_waits_and_can_choose_another() -> None:
    source = Path(
        "mps/gui/photo_history.py"
    ).read_text(encoding="utf-8")

    assert 'text="Choose another photograph"' in source
    assert "self._window.lift()" in source
    assert "self._window.focus_force()" in source
    assert "self._window.wait_window()" in source
    assert "return dialog.choose_another" in source


def test_app_uses_photo_history_dialog_instead_of_terminal() -> None:
    source = Path(
        "mps/gui/app.py"
    ).read_text(encoding="utf-8")

    assert "show_photo_history as show_photo_history_dialog" in source
    assert "choose_another = show_photo_history_dialog(" in source
    assert "Select a photograph for Photo History" in source
