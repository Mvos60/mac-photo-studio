# Sprint 008.2 — Duplicate Summary Reporting

This sprint adds a reporting layer on top of SHA-256 duplicate detection.

## Added

- `mps/models/duplicate_summary.py`
- `mps/services/duplicate_reporter.py`
- `tests/test_duplicate_reporter.py`

The package also carries `mps/models/duplicate_result.py` as a safety dependency, so a partial previous install cannot break this sprint.

## Behaviour

The reporter counts duplicate-check results into four groups:

- checked files
- new files where the destination does not exist
- already imported files where source and destination are identical
- conflicts where the destination exists but has different content

The summary exposes `safe_to_continue`, which is only true when there are no conflicts.

## Safety

This sprint does not copy, delete, rename, or overwrite photo files.
It only summarizes duplicate-check results.
