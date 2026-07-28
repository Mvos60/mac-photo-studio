from pathlib import Path
from types import SimpleNamespace

from mps.gui.culling_review import (
    build_confirmation_message,
    execute_selected_candidates,
    execution_totals,
    result_detail_text,
    result_status_text,
)
from mps.services.culling_executor import (
    CullingExecutionResult,
)


def make_result(
    *,
    stem: str,
    success: bool,
    raw: bool = False,
    manifest: int = 0,
    index: int = 0,
    provenance: int = 0,
    message: str = "ok",
) -> CullingExecutionResult:
    return CullingExecutionResult(
        success=success,
        stem=stem,
        raw_quarantine_path=(
            Path("/tmp/quarantine") / f"{stem}.ARW"
            if raw
            else None
        ),
        removed_manifest_entries=manifest,
        removed_index_entries=index,
        quarantined_provenance_items=provenance,
        message=message,
    )


def test_execute_selected_candidates_preserves_order():
    candidates = (
        SimpleNamespace(stem="A"),
        SimpleNamespace(stem="B"),
    )
    calls = []

    def executor(session, candidate):
        calls.append((Path(session), candidate.stem))
        return make_result(
            stem=candidate.stem,
            success=True,
        )

    results = execute_selected_candidates(
        Path("/photos/session"),
        candidates,
        executor=executor,
    )

    assert tuple(result.stem for result in results) == (
        "A",
        "B",
    )
    assert calls == [
        (Path("/photos/session"), "A"),
        (Path("/photos/session"), "B"),
    ]


def test_confirmation_message_describes_safe_operation():
    candidates = (
        SimpleNamespace(stem="A"),
        SimpleNamespace(stem="B"),
    )

    message = build_confirmation_message(candidates)

    assert "2 selected candidate(s)" in message
    assert "Nothing will be permanently deleted" in message
    assert "transactionally" in message
    assert "Safe Quarantine" in message


def test_execution_totals_count_successful_results_only():
    results = (
        make_result(
            stem="A",
            success=True,
            raw=True,
            manifest=2,
            index=2,
            provenance=4,
        ),
        make_result(
            stem="B",
            success=True,
            manifest=1,
            index=1,
            provenance=2,
        ),
        make_result(
            stem="C",
            success=False,
            manifest=99,
            index=99,
            provenance=99,
        ),
    )

    assert execution_totals(results) == {
        "successful": 2,
        "failed": 1,
        "raws": 1,
        "manifest": 3,
        "index": 3,
        "provenance": 6,
    }


def test_result_status_text():
    assert result_status_text(
        make_result(stem="A", success=True)
    ) == "SUCCESS"

    assert result_status_text(
        make_result(stem="B", success=False)
    ) == "FAILED"


def test_success_result_detail_contains_quarantine_counts():
    result = make_result(
        stem="A",
        success=True,
        raw=True,
        manifest=2,
        index=2,
        provenance=4,
        message="Quarantined successfully",
    )

    detail = result_detail_text(result)

    assert "Status: SUCCESS" in detail
    assert "Quarantined successfully" in detail
    assert "RAW quarantine:" in detail
    assert "Manifest entries removed: 2" in detail
    assert "Index entries removed: 2" in detail
    assert "Provenance items moved: 4" in detail


def test_failed_result_detail_does_not_claim_changes():
    result = make_result(
        stem="B",
        success=False,
        manifest=2,
        index=2,
        provenance=4,
        message="RAW hash changed",
    )

    detail = result_detail_text(result)

    assert "Status: FAILED" in detail
    assert "RAW hash changed" in detail
    assert "Manifest entries removed" not in detail
    assert "Index entries removed" not in detail
    assert "Provenance items moved" not in detail
