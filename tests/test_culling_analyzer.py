import hashlib
from pathlib import Path

from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.culling_analyzer import analyze_culling
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index


def _settings() -> Settings:
    return Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
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
        created_at="2026-07-15T08:00:00+00:00",
    )


def _write_identity_index(
    import_root: Path,
    entries: list[ProvenanceCertificateIndexEntry],
) -> None:
    write_index(
        ProvenanceCertificateIndex(
            entries=entries,
        ),
        index_path(import_root),
    )


def test_existing_raw_and_jpeg_are_not_culling_candidates(
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
                provenance_id="MPS-PROV-RAW-1",
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id="MPS-PROV-JPEG-1",
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 0
    assert result.orphan_raw_candidate_count == 0
    assert result.missing_jpegs == []


def test_deleted_jpeg_with_verified_surviving_raw_is_detected(
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
                provenance_id="MPS-PROV-RAW-1",
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id="MPS-PROV-JPEG-1",
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert result.orphan_raw_candidate_count == 1

    candidate = result.missing_jpegs[0]

    assert candidate.stem == "DSC0001"
    assert candidate.jpeg_path == jpeg
    assert (
        candidate.jpeg_provenance_id
        == "MPS-PROV-JPEG-1"
    )
    assert candidate.raw_path == raw
    assert candidate.raw_hash_matches is True
    assert candidate.has_surviving_raw is True
    assert candidate.is_orphan_raw_candidate is True


def test_modified_surviving_raw_is_not_culling_candidate(
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
                provenance_id="MPS-PROV-RAW-1",
                sha256=_sha256(b"original raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id="MPS-PROV-JPEG-1",
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert result.orphan_raw_candidate_count == 0

    candidate = result.missing_jpegs[0]

    assert candidate.has_surviving_raw is True
    assert candidate.raw_hash_matches is False
    assert candidate.is_orphan_raw_candidate is False


def test_missing_jpeg_without_imported_raw_is_reported_but_not_candidate(
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
                provenance_id="MPS-PROV-JPEG-1",
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert result.orphan_raw_candidate_count == 0

    candidate = result.missing_jpegs[0]

    assert candidate.raw_path is None
    assert candidate.raw_provenance_id is None
    assert candidate.raw_sha256 is None
    assert candidate.raw_hash_matches is False
    assert candidate.is_orphan_raw_candidate is False


def test_deleted_raw_and_jpeg_are_not_candidate(
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
                provenance_id="MPS-PROV-RAW-1",
                sha256=_sha256(b"raw"),
            ),
            _entry(
                path=jpeg,
                provenance_id="MPS-PROV-JPEG-1",
                sha256=_sha256(b"jpeg"),
            ),
        ],
    )

    result = analyze_culling(
        import_root,
        _settings(),
    )

    assert result.missing_jpeg_count == 1
    assert result.orphan_raw_candidate_count == 0
    assert (
        result.missing_jpegs[0].is_orphan_raw_candidate
        is False
    )


def test_multiple_deleted_jpegs_are_reported_in_stem_order(
    tmp_path: Path,
):
    import_root = tmp_path / "Session"
    import_root.mkdir()

    entries = []

    for number in (3, 1, 2):
        stem = f"DSC{number:04d}"
        raw = import_root / f"{stem}.ARW"
        jpeg = import_root / f"{stem}.JPG"
        raw_content = f"raw-{number}".encode()

        raw.write_bytes(raw_content)

        entries.extend(
            [
                _entry(
                    path=raw,
                    provenance_id=(
                        f"MPS-PROV-RAW-{number}"
                    ),
                    sha256=_sha256(raw_content),
                ),
                _entry(
                    path=jpeg,
                    provenance_id=(
                        f"MPS-PROV-JPEG-{number}"
                    ),
                    sha256=_sha256(
                        f"jpeg-{number}".encode()
                    ),
                ),
            ]
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

    assert result.orphan_raw_candidate_count == 3


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
    assert result.orphan_raw_candidate_count == 0
    assert result.missing_jpegs == []
