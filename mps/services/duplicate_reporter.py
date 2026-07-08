from collections.abc import Iterable

from mps.models.duplicate_result import DuplicateResult
from mps.models.duplicate_summary import DuplicateSummary


def summarize_duplicates(results: Iterable[DuplicateResult]) -> DuplicateSummary:
    checked = 0
    missing = 0
    identical = 0
    conflicts = 0

    for result in results:
        checked += 1

        if not result.exists:
            missing += 1
        elif result.identical:
            identical += 1
        elif result.conflict:
            conflicts += 1

    return DuplicateSummary(
        checked=checked,
        missing=missing,
        identical=identical,
        conflicts=conflicts,
    )


def format_duplicate_summary(summary: DuplicateSummary) -> str:
    status = "SAFE" if summary.safe_to_continue else "CONFLICTS FOUND"

    return "\n".join(
        [
            "Duplicate check summary",
            "-----------------------",
            f"Status: {status}",
            f"Checked: {summary.checked}",
            f"New files: {summary.missing}",
            f"Already imported: {summary.identical}",
            f"Conflicts: {summary.conflicts}",
        ]
    )
