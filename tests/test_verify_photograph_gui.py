from mps.gui.verify_photograph import (
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
