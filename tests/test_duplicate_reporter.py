from mps.models.duplicate_result import DuplicateResult
from mps.services.duplicate_reporter import format_duplicate_summary, summarize_duplicates


def test_duplicate_summary_counts_all_result_types():
    results = [
        DuplicateResult(exists=False, identical=False, conflict=False),
        DuplicateResult(exists=True, identical=True, conflict=False),
        DuplicateResult(exists=True, identical=False, conflict=True),
    ]

    summary = summarize_duplicates(results)

    assert summary.checked == 3
    assert summary.missing == 1
    assert summary.identical == 1
    assert summary.conflicts == 1
    assert summary.safe_to_continue is False


def test_duplicate_summary_is_safe_when_no_conflicts():
    results = [
        DuplicateResult(exists=False, identical=False, conflict=False),
        DuplicateResult(exists=True, identical=True, conflict=False),
    ]

    summary = summarize_duplicates(results)

    assert summary.checked == 2
    assert summary.conflicts == 0
    assert summary.safe_to_continue is True


def test_duplicate_summary_handles_empty_results():
    summary = summarize_duplicates([])

    assert summary.checked == 0
    assert summary.missing == 0
    assert summary.identical == 0
    assert summary.conflicts == 0
    assert summary.safe_to_continue is True


def test_format_duplicate_summary_reports_safe_status():
    summary = summarize_duplicates(
        [
            DuplicateResult(exists=False, identical=False, conflict=False),
            DuplicateResult(exists=True, identical=True, conflict=False),
        ]
    )

    text = format_duplicate_summary(summary)

    assert "Status: SAFE" in text
    assert "Checked: 2" in text
    assert "New files: 1" in text
    assert "Already imported: 1" in text
    assert "Conflicts: 0" in text


def test_format_duplicate_summary_reports_conflict_status():
    summary = summarize_duplicates(
        [
            DuplicateResult(exists=True, identical=False, conflict=True),
        ]
    )

    text = format_duplicate_summary(summary)

    assert "Status: CONFLICTS FOUND" in text
    assert "Conflicts: 1" in text
