from pathlib import Path

from mps.models.import_progress import ImportProgress
from mps.services.import_progress_output import (
    format_import_progress,
    print_import_progress,
)


def _progress(
    *,
    phase: str = "checking",
    current: int = 2,
    total: int = 4,
) -> ImportProgress:
    return ImportProgress(
        current=current,
        total=total,
        source=Path("/media/card/MAC02638.JPG"),
        destination=Path("/home/mac/Pictures"),
        phase=phase,
    )


def test_format_import_progress_shows_phase_bar_and_filename() -> None:
    text = format_import_progress(
        _progress()
    )

    assert text.startswith(
        "[1/4] Checking card"
    )
    assert "2/4" in text
    assert "50%" in text
    assert "MAC02638.JPG" in text
    assert "██████████░░░░░░░░░░" in text


def test_format_verification_progress_hides_filename() -> None:
    text = format_import_progress(
        _progress(
            phase="verifying",
            current=0,
            total=1,
        )
    )

    assert text.startswith(
        "[4/4] Verifying import"
    )
    assert "0/1" in text
    assert "0%" in text
    assert "MAC02638.JPG" not in text


def test_print_import_progress_writes_visible_line(
    capsys,
) -> None:
    print_import_progress(_progress())

    output = capsys.readouterr().out

    assert "[1/4] Checking card" in output
    assert "MAC02638.JPG" in output
    assert "50%" in output
