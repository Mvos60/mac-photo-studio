from pathlib import Path

from mps.gui.verify_photograph import (
    VerifyPhotographDialog,
    verification_state,
)


def test_verification_state_trusted() -> None:
    state, explanation = verification_state(
        0,
        "Status: VERIFIED",
    )

    assert state == "Trusted"
    assert "matches" in explanation


def test_verification_state_changed() -> None:
    state, explanation = verification_state(
        1,
        "HASH MISMATCH",
    )

    assert state == "Changed or invalid"
    assert "does not fully match" in explanation


def test_verification_state_not_managed() -> None:
    state, explanation = verification_state(
        1,
        "No certificate found",
    )

    assert state == "Not managed by MPS"
    assert "provenance record" in explanation


def test_verification_state_fallback() -> None:
    state, _explanation = verification_state(
        1,
        "Unexpected verification error",
    )

    assert state == "Verification unavailable"


def test_verify_dialog_uses_mps_dialog_framework() -> None:
    source = Path(
        "mps/gui/verify_photograph.py"
    ).read_text(encoding="utf-8")

    assert "MpsDialog(" in source
    assert "self._dialog.add_header(" in source
    assert "self._dialog.create_section(" in source
    assert "self._dialog.add_close_button()" in source
    assert "self._dialog.show()" in source
    assert "tk.Toplevel(" not in source


def test_verify_dialog_is_raised_and_waits_until_closed() -> None:
    source = Path(
        "mps/gui/verify_photograph.py"
    ).read_text(encoding="utf-8")

    assert "self._window.lift()" in source
    assert "self._window.focus_force()" in source
    assert "self._window.wait_window()" in source


def test_verify_dialog_offers_choose_another_photograph() -> None:
    source = Path(
        "mps/gui/verify_photograph.py"
    ).read_text(encoding="utf-8")

    assert 'text="Choose another photograph"' in source
    assert "self._choose_another = False" in source
    assert "self._choose_another = True" in source
    assert "return dialog.choose_another" in source


def test_verify_workflow_reopens_picker_when_requested() -> None:
    source = Path(
        "mps/gui/app.py"
    ).read_text(encoding="utf-8")

    assert "while True:" in source
    assert "choose_another = show_verify_photograph(" in source
    assert "if not choose_another:" in source
