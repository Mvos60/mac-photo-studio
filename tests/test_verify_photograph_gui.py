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

    assert state == "TRUSTED"
    assert "matches" in explanation


def test_verification_state_changed() -> None:
    state, explanation = verification_state(
        1,
        "HASH MISMATCH",
    )

    assert state == "CHANGED OR INVALID"
    assert "does not fully match" in explanation


def test_verification_state_not_managed() -> None:
    state, explanation = verification_state(
        1,
        "No certificate found",
    )

    assert state == "NOT MANAGED BY MPS"
    assert "verified MPS import" in explanation
    assert "does not mean" in explanation
    assert "AI-generated" in explanation


def test_verification_state_fallback() -> None:
    state, _explanation = verification_state(
        1,
        "Unexpected verification error",
    )

    assert state == "VERIFICATION UNAVAILABLE"


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


def test_verification_state_managed_import_reason_is_not_managed() -> None:
    state, explanation = verification_state(
        1,
        (
            "Status: NOT TRUSTED\n"
            "Reason: Photo is not inside a managed provenance import"
        ),
    )

    assert state == "NOT MANAGED BY MPS"
    assert "verified MPS import" in explanation
    assert "altered" in explanation
    assert "AI-generated" in explanation


def test_verification_state_identity_mismatch_remains_changed() -> None:
    state, explanation = verification_state(
        1,
        "Actual file SHA-256 does not match recorded identity",
    )

    assert state == "CHANGED OR INVALID"
    assert "does not fully match" in explanation


def test_verify_dialog_labels_raw_verification_details() -> None:
    source = Path(
        "mps/gui/verify_photograph.py"
    ).read_text(encoding="utf-8")

    assert 'title="Raw Verification Details"' in source
    assert 'title="Technical details"' not in source


def test_verify_and_history_use_same_status_section_title() -> None:
    verify_source = Path(
        "mps/gui/verify_photograph.py"
    ).read_text(encoding="utf-8")
    history_source = Path(
        "mps/gui/photo_history.py"
    ).read_text(encoding="utf-8")

    assert 'title="MPS Status"' in verify_source
    assert 'title="MPS Status"' in history_source
    assert 'title="Verification result"' not in verify_source
    assert 'title="History status"' not in history_source
