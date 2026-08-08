from datetime import date, datetime
from pathlib import Path

from mps.models.import_photo_selection import (
    ImportPhotoCandidate,
    summarize_import_photo_selection,
)


def candidate(key, captured_at=None, conflict=False):
    return ImportPhotoCandidate(
        key, key.upper(), raw_paths=(Path(f"{key}.ARW"),),
        captured_at=captured_at, captured_at_conflict=conflict,
    )


def test_candidate_formats_capture_time_and_conflict():
    assert candidate("a", datetime(2026, 6, 10, 14, 31)).display_captured_at == "10-06-2026 14:31"
    assert candidate("a").display_captured_at == "—"
    assert candidate("a", conflict=True).display_captured_at == "⚠ conflict"


def test_summary_reports_range_dates_unknown_conflict_and_mismatch():
    candidates = (
        candidate("a", datetime(2026, 6, 10, 14, 31)),
        candidate("b", datetime(2026, 6, 11, 0, 14)),
        candidate("c"), candidate("d", conflict=True),
        candidate("e", datetime(2026, 6, 12, 9, 0)),
    )
    summary = summarize_import_photo_selection(candidates, {"a", "b", "c", "d"}, date(2026, 6, 10))
    assert summary.selected_count == 4
    assert summary.earliest == datetime(2026, 6, 10, 14, 31)
    assert summary.latest == datetime(2026, 6, 11, 0, 14)
    assert summary.unique_dates == frozenset({date(2026, 6, 10), date(2026, 6, 11)})
    assert summary.unknown_count == 1
    assert summary.conflict_count == 1
    assert summary.mismatch_count == 1


def test_summary_changes_with_selection_and_empty_is_safe():
    candidates = (candidate("a", datetime(2026, 6, 10, 14)), candidate("b", datetime(2026, 6, 12, 9)))
    selected = summarize_import_photo_selection(candidates, {"a"}, date(2026, 6, 10))
    empty = summarize_import_photo_selection(candidates, set(), date(2026, 6, 10))
    assert selected.mismatch_count == 0
    assert selected.unique_dates == frozenset({date(2026, 6, 10)})
    assert empty.selected_count == 0
    assert empty.earliest is None and empty.latest is None
    assert empty.unique_dates == frozenset()
