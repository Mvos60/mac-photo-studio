from pathlib import Path

from mps.gui.culling_review import (
    actionable_candidates,
    candidate_details,
    candidate_title,
)
from mps.services.culling_analyzer import (
    CullingAnalysis,
    CullingCandidateStatus,
    MissingImportedJpeg,
)


def candidate(
    tmp_path: Path,
    *,
    stem: str = "MAC00001",
    raw_path: Path | None,
    raw_hash_matches: bool,
) -> MissingImportedJpeg:
    return MissingImportedJpeg(
        stem=stem,
        jpeg_path=tmp_path / f"{stem}.JPG",
        jpeg_provenance_id="jpeg-prov",
        jpeg_sha256="jpeg-sha",
        raw_path=raw_path,
        raw_provenance_id=(
            "raw-prov"
            if raw_path is not None
            else None
        ),
        raw_sha256=(
            "raw-sha"
            if raw_path is not None
            else None
        ),
        raw_hash_matches=raw_hash_matches,
    )


def test_actionable_candidates_filters_items(
    tmp_path: Path,
):
    raw_one = tmp_path / "MAC00001.ARW"
    raw_one.write_bytes(b"raw-one")
    raw_two = tmp_path / "MAC00002.ARW"
    raw_two.write_bytes(b"raw-two")

    actionable = candidate(
        tmp_path,
        raw_path=raw_one,
        raw_hash_matches=True,
    )
    mismatch = candidate(
        tmp_path,
        stem="MAC00002",
        raw_path=raw_two,
        raw_hash_matches=False,
    )

    analysis = CullingAnalysis(
        import_root=tmp_path,
        missing_jpegs=[actionable, mismatch],
    )

    assert actionable_candidates(analysis) == (
        actionable,
    )


def test_candidate_title_uses_raw_filename(
    tmp_path: Path,
):
    raw = tmp_path / "MAC00001.ARW"

    item = candidate(
        tmp_path,
        raw_path=raw,
        raw_hash_matches=True,
    )

    assert candidate_title(item) == "MAC00001.ARW"


def test_candidate_title_falls_back_to_stem(
    tmp_path: Path,
):
    item = candidate(
        tmp_path,
        raw_path=None,
        raw_hash_matches=False,
    )

    assert candidate_title(item) == "MAC00001"


def test_candidate_details_for_raw_candidate(
    tmp_path: Path,
):
    raw = tmp_path / "MAC00001.ARW"
    raw.write_bytes(b"raw")

    item = candidate(
        tmp_path,
        raw_path=raw,
        raw_hash_matches=True,
    )

    assert (
        item.status
        == CullingCandidateStatus.CULL_CANDIDATE
    )
    assert "RAW verified" in candidate_details(item)


def test_candidate_details_for_provenance_candidate(
    tmp_path: Path,
):
    item = candidate(
        tmp_path,
        raw_path=None,
        raw_hash_matches=False,
    )

    assert (
        item.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    )
    assert "provenance cleanup" in (
        candidate_details(item)
    )


def test_culling_review_uses_title_case_for_failure_dialog() -> None:
    source = Path(
        "mps/gui/culling_review.py"
    ).read_text(encoding="utf-8")

    assert '"Safe Quarantine Failed"' in source
    assert '"Safe Quarantine failed"' not in source
