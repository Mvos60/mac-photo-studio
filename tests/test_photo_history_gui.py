from pathlib import Path

from mps.gui.photo_history import (
    PhotoHistoryDialog,
    history_state,
)


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
    assert "could not display" in explanation


def test_photo_history_dialog_uses_mps_framework() -> None:
    source = Path(
        "mps/gui/photo_history.py"
    ).read_text(encoding="utf-8")

    assert "MpsDialog(" in source
    assert "self._dialog.add_header(" in source
    assert "self._dialog.create_section(" in source
    assert 'title="Recorded provenance history"' in source
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
