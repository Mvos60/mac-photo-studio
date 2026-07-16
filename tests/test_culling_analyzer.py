import hashlib
from pathlib import Path

from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.culling_analyzer import (
    CullingCandidateStatus,
    analyze_culling,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index


def _settings() -> Settings:
    return Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": [
                    "JPG",
                    "JPEG",
                ],
            }
        }
    )


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _entry(
    *,
    path: Path,
    provenance_id: str,
    sha256: str,
) -> ProvenanceCertificateIndexEntry:
    return ProvenanceCertificateIndexEntry(
        certificate_id=(
            f"MPS-CERT-{provenance_id}"
        ),
        provenance_id=provenance_id,
        session_id="MPS-SESSION-1",
        destination_path=str(path),
        certificate_path=str(
            path.parent
            / "provenance"
            / f"MPS-CERT-{provenance_id}.json"
        ),
        sha256=sha256,
        camera_model="ILCE-7M3",
        created_at=(
            "2026-07-15T08:00:00+00:00"
        ),
    )


def _write_identity_index(
    import_root: Path,
    entries: list[
        ProvenanceCertificateIndexEntry
    ],
) -> None:
    write_index(
        ProvenanceCertificateIndex(
            entries=entries,
        ),
        index_path(import_root),
    )


def test_existing_raw_and_jpeg_are_not_candidates(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"

    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"raw")
    jpeg.write_bytes(b"jpeg")

    _write_identity_index(
        import_root,
        [
            _entry(
                path=raw,
                provenance_id=(
                    "MPS-PROV-RAW-1"
                ),
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 0
    assert (
        result.orphan_raw_candidate_count
        == 0
    )
    assert (
        result.provenance_cleanup_candidate_count
        == 0
    )
    assert result.actionable_candidate_count == 0


def test_deleted_jpeg_with_verified_raw_is_cull_candidate(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"

    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"raw")

    _write_identity_index(
        import_root,
        [
            _entry(
                path=raw,
                provenance_id=(
                    "MPS-PROV-RAW-1"
                ),
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert (
        result.orphan_raw_candidate_count
        == 1
    )
    assert (
        result.provenance_cleanup_candidate_count
        == 0
    )
    assert result.actionable_candidate_count == 1

    candidate = result.missing_jpegs[0]

    assert (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    )
    assert candidate.is_orphan_raw_candidate
    assert not (
        candidate.is_provenance_cleanup_candidate
    )
    assert candidate.is_actionable


def test_deleted_jpeg_without_imported_raw_is_cleanup_candidate(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()

    _write_identity_index(
        import_root,
        [
            _entry(
                path=jpeg,
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert (
        result.orphan_raw_candidate_count
        == 0
    )
    assert (
        result.provenance_cleanup_candidate_count
        == 1
    )
    assert result.actionable_candidate_count == 1

    candidate = result.missing_jpegs[0]

    assert candidate.raw_path is None
    assert not candidate.has_imported_raw
    assert (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    )
    assert not candidate.is_orphan_raw_candidate
    assert (
        candidate.is_provenance_cleanup_candidate
    )
    assert candidate.is_actionable


def test_modified_surviving_raw_is_hash_mismatch(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"

    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"modified raw")

    _write_identity_index(
        import_root,
        [
            _entry(
                path=raw,
                provenance_id=(
                    "MPS-PROV-RAW-1"
                ),
                sha256=_sha256(
                    b"original raw"
                ),
            ),
            _entry(
                path=jpeg,
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    candidate = result.missing_jpegs[0]

    assert (
        candidate.status
        == (
            CullingCandidateStatus
            .RAW_HASH_MISMATCH
        )
    )
    assert candidate.has_surviving_raw
    assert not candidate.raw_hash_matches
    assert not candidate.is_actionable


def test_deleted_raw_and_jpeg_require_no_action(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"

    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()

    _write_identity_index(
        import_root,
        [
            _entry(
                path=raw,
                provenance_id=(
                    "MPS-PROV-RAW-1"
                ),
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    candidate = result.missing_jpegs[0]

    assert candidate.has_imported_raw
    assert not candidate.has_surviving_raw
    assert (
        candidate.status
        == CullingCandidateStatus.NO_ACTION
    )
    assert not candidate.is_actionable


def test_actionable_candidate_lists_are_separate(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"
    import_root.mkdir()

    raw = import_root / "DSC0001.ARW"
    raw.write_bytes(b"raw")

    _write_identity_index(
        import_root,
        [
            _entry(
                path=raw,
                provenance_id=(
                    "MPS-PROV-RAW-1"
                ),
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=(
                    import_root
                    / "DSC0001.JPG"
                ),
                provenance_id=(
                    "MPS-PROV-JPEG-1"
                ),
                sha256=_sha256(b"jpeg-1"),
            ),
            _entry(
                path=(
                    import_root
                    / "DSC0002.JPG"
                ),
                provenance_id=(
                    "MPS-PROV-JPEG-2"
                ),
                sha256=_sha256(b"jpeg-2"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert [
        item.stem
        for item in result.orphan_raw_candidates
    ] == [
        "DSC0001",
    ]

    assert [
        item.stem
        for item in (
            result.provenance_cleanup_candidates
        )
    ] == [
        "DSC0002",
    ]

    assert [
        item.stem
        for item in result.actionable_candidates
    ] == [
        "DSC0001",
        "DSC0002",
    ]


def test_multiple_missing_jpegs_are_sorted_by_stem(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"
    import_root.mkdir()

    entries = []

    for number in (3, 1, 2):
        jpeg = (
            import_root
            / f"DSC{number:04d}.JPG"
        )

        entries.append(
            _entry(
                path=jpeg,
                provenance_id=(
                    f"MPS-PROV-JPEG-{number}"
                ),
                sha256=_sha256(
                    f"jpeg-{number}".encode()
                ),
            )
        )

    _write_identity_index(
        import_root,
        entries,
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert [
        candidate.stem
        for candidate in result.missing_jpegs
    ] == [
        "DSC0001",
        "DSC0002",
        "DSC0003",
    ]

    assert (
        result.provenance_cleanup_candidate_count
        == 3
    )


def test_analysis_without_certificate_index_is_empty(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"
    import_root.mkdir()

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 0
    assert (
        result.orphan_raw_candidate_count
        == 0
    )
    assert (
        result.provenance_cleanup_candidate_count
        == 0
    )
    assert result.actionable_candidate_count == 0
