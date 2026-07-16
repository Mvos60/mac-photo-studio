from pathlib import Path

from mps.services.culling_analyzer import (
    CullingAnalysis,
    MissingImportedJpeg,
)
from mps.services.culling_report import build_culling_report


def _candidate(
    *,
    stem: str = "DSC0001",
    raw_imported: bool = True,
    raw_exists: bool = True,
    raw_hash_matches: bool = True,
    tmp_path: Path,
) -> MissingImportedJpeg:
    raw_path = (
        tmp_path / f"{stem}.ARW"
        if raw_imported
        else None
    )

    if raw_path is not None and raw_exists:
        raw_path.write_bytes(b"raw")

    return MissingImportedJpeg(
        stem=stem,
        jpeg_path=tmp_path / f"{stem}.JPG",
        jpeg_provenance_id="MPS-PROV-JPEG-1",
        jpeg_sha256="jpeg-hash",
        raw_path=raw_path,
        raw_provenance_id=(
            "MPS-PROV-RAW-1"
            if raw_imported
            else None
        ),
        raw_sha256=(
            "raw-hash"
            if raw_imported
            else None
        ),
        raw_hash_matches=raw_hash_matches,
    )


def test_empty_culling_report(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[],
        )
    )

    assert "Missing imported JPGs          : 0" in report
    assert "Verified orphan RAWs           : 0" in report
    assert "Provenance cleanup candidates  : 0" in report
    assert (
        "No missing imported JPG files were detected."
        in report
    )


def test_report_marks_verified_raw_cull_candidate(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[
                _candidate(
                    tmp_path=tmp_path,
                )
            ],
        )
    )

    assert "DSC0001" in report
    assert "CULL CANDIDATE" in report
    assert "Verified orphan RAWs           : 1" in report
    assert "Provenance cleanup candidates  : 0" in report


def test_report_marks_jpeg_only_cleanup_candidate(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[
                _candidate(
                    tmp_path=tmp_path,
                    raw_imported=False,
                    raw_exists=False,
                    raw_hash_matches=False,
                )
            ],
        )
    )

    assert "PROVENANCE CLEANUP CANDIDATE" in report
    assert "Verified orphan RAWs           : 0" in report
    assert "Provenance cleanup candidates  : 1" in report


def test_report_blocks_raw_hash_mismatch(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[
                _candidate(
                    tmp_path=tmp_path,
                    raw_hash_matches=False,
                )
            ],
        )
    )

    assert "BLOCKED: RAW HASH MISMATCH" in report


def test_report_marks_missing_imported_raw_as_no_action(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[
                _candidate(
                    tmp_path=tmp_path,
                    raw_imported=True,
                    raw_exists=False,
                    raw_hash_matches=False,
                )
            ],
        )
    )

    assert "NO ACTION: IMPORTED RAW IS MISSING" in report


def test_report_states_read_only(
    tmp_path: Path,
):
    report = build_culling_report(
        CullingAnalysis(
            import_root=tmp_path,
            missing_jpegs=[],
        )
    )

    assert (
        "Read-only analysis. No files were changed."
        in report
    )
