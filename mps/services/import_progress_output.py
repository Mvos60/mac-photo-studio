from __future__ import annotations

import sys

from mps.models.import_progress import ImportProgress

_BAR_WIDTH = 20
_PHASES = {
    "checking": (1, "Checking card"),
    "copying": (2, "Copying photos"),
    "provenance": (3, "Recording provenance"),
    "verifying": (4, "Verifying import"),
}
_PHASE_TOTAL = 4


def _progress_bar(percent: int) -> str:
    filled = (
        max(0, min(percent, 100))
        * _BAR_WIDTH
        // 100
    )

    return (
        "█" * filled
        + "░" * (_BAR_WIDTH - filled)
    )


def format_import_progress(
    progress: ImportProgress,
) -> str:
    phase_number, label = _PHASES.get(
        progress.phase,
        (
            2,
            progress.phase.replace(
                "_",
                " ",
            ).title(),
        ),
    )

    line = (
        f"[{phase_number}/{_PHASE_TOTAL}] "
        f"{label:<21} "
        f"{progress.current:>3}/{progress.total:<3} "
        f"[{_progress_bar(progress.percent)}] "
        f"{progress.percent:>3}%"
    )

    if (
        progress.phase != "verifying"
        and progress.source.name
    ):
        line += f" — {progress.source.name}"

    return line


def print_import_progress(
    progress: ImportProgress,
) -> None:
    line = format_import_progress(progress)

    if not sys.stdout.isatty():
        print(line, flush=True)
        return

    completed = (
        progress.total <= 0
        or progress.current >= progress.total
    )

    print(
        "\r" + line.ljust(120),
        end="\n" if completed else "",
        flush=True,
    )
