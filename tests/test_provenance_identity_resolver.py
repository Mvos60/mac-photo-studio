from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.provenance_identity_resolver import (
    resolve_provenance_identity,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index


def _entry(
    *,
    certificate_id: str,
    provenance_id: str,
    destination_path: str,
    sha256: str,
) -> ProvenanceCertificateIndexEntry:
    return ProvenanceCertificateIndexEntry(
        certificate_id=certificate_id,
        provenance_id=provenance_id,
        session_id="MPS-SESSION-001",
        destination_path=destination_path,
        certificate_path=(
            f"/photos/provenance/{certificate_id}.json"
        ),
        sha256=sha256,
        camera_model="ILCE-7M3",
        created_at="2026-07-13T10:00:00+00:00",
    )


def _write_index(
    tmp_path,
    entries: list[ProvenanceCertificateIndexEntry],
) -> None:
    write_index(
        ProvenanceCertificateIndex(
            entries=entries,
        ),
        index_path(tmp_path),
    )


def test_resolve_identity_by_photo_path(tmp_path):
    entry = _entry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        destination_path="/photos/DSC0001.ARW",
        sha256="raw-hash-001",
    )

    _write_index(
        tmp_path,
        [entry],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
    )

    assert result.resolved is True
    assert result.provenance_id == "MPS-PROV-001"
    assert result.certificate_id == "MPS-CERT-001"
    assert result.destination_path == "/photos/DSC0001.ARW"
    assert result.sha256 == "raw-hash-001"
    assert result.errors == []


def test_resolve_identity_by_sha256(tmp_path):
    entry = _entry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        destination_path="/photos/DSC0001.ARW",
        sha256="raw-hash-001",
    )

    _write_index(
        tmp_path,
        [entry],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        sha256="raw-hash-001",
    )

    assert result.resolved is True
    assert result.provenance_id == "MPS-PROV-001"
    assert result.sha256 == "raw-hash-001"


def test_resolve_identity_by_path_and_sha256(tmp_path):
    entry = _entry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        destination_path="/photos/DSC0001.ARW",
        sha256="raw-hash-001",
    )

    _write_index(
        tmp_path,
        [entry],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
        sha256="raw-hash-001",
    )

    assert result.resolved is True
    assert result.provenance_id == "MPS-PROV-001"


def test_path_and_sha256_must_match_same_identity(tmp_path):
    first = _entry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        destination_path="/photos/DSC0001.ARW",
        sha256="raw-hash-001",
    )

    second = _entry(
        certificate_id="MPS-CERT-002",
        provenance_id="MPS-PROV-002",
        destination_path="/photos/DSC0002.ARW",
        sha256="raw-hash-002",
    )

    _write_index(
        tmp_path,
        [first, second],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
        sha256="raw-hash-002",
    )

    assert result.resolved is False
    assert result.provenance_id is None
    assert result.errors == [
        "No matching provenance identity found"
    ]


def test_resolve_identity_requires_search_value(tmp_path):
    result = resolve_provenance_identity(
        import_root=tmp_path,
    )

    assert result.resolved is False
    assert result.errors == [
        "photo_path or sha256 is required"
    ]


def test_resolve_identity_requires_certificate_index(tmp_path):
    result = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
    )

    assert result.resolved is False
    assert result.errors == [
        "Provenance certificate index does not exist"
    ]


def test_resolve_identity_reports_missing_match(tmp_path):
    _write_index(
        tmp_path,
        [
            _entry(
                certificate_id="MPS-CERT-001",
                provenance_id="MPS-PROV-001",
                destination_path="/photos/DSC0001.ARW",
                sha256="raw-hash-001",
            )
        ],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path="/photos/UNKNOWN.ARW",
    )

    assert result.resolved is False
    assert result.errors == [
        "No matching provenance identity found"
    ]


def test_resolve_identity_rejects_ambiguous_sha256(tmp_path):
    first = _entry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        destination_path="/photos/DSC0001.ARW",
        sha256="same-hash",
    )

    second = _entry(
        certificate_id="MPS-CERT-002",
        provenance_id="MPS-PROV-002",
        destination_path="/photos/DSC0002.ARW",
        sha256="same-hash",
    )

    _write_index(
        tmp_path,
        [first, second],
    )

    result = resolve_provenance_identity(
        import_root=tmp_path,
        sha256="same-hash",
    )

    assert result.resolved is False
    assert result.provenance_id is None
    assert result.errors == [
        "Multiple matching provenance identities found"
    ]
