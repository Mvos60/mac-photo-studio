import hashlib
from pathlib import Path

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.culling_analyzer import MissingImportedJpeg
from mps.services.culling_executor import (
    execute_culling_candidate,
)
from mps.services.manifest_writer import (
    add_file_entry,
    create_manifest,
    load_manifest,
    write_manifest_to_path,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import (
    load_index,
    write_index,
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _index_entry(
    *,
    path: Path,
    provenance_id: str,
    certificate_path: Path,
    sha256: str,
) -> ProvenanceCertificateIndexEntry:
    return ProvenanceCertificateIndexEntry(
        certificate_id=f"CERT-{provenance_id}",
        provenance_id=provenance_id,
        session_id="MPS-SESSION-1",
        destination_path=str(path),
        certificate_path=str(certificate_path),
        sha256=sha256,
        camera_model="ILCE-7M3",
        created_at="2026-07-15T08:00:00+00:00",
    )


def _build_session(
    tmp_path: Path,
) -> tuple[
    Path,
    MissingImportedJpeg,
]:
    root = tmp_path / "Session"
    root.mkdir()

    raw = root / "DSC0001.ARW"
    jpeg = root / "DSC0001.JPG"

    raw_content = b"trusted raw"
    jpeg_content = b"trusted jpeg"

    raw.write_bytes(raw_content)

    manifest = create_manifest(
        project="Adriatic",
        day_session="03_Slovenia",
        mps_version="0.2.0",
        session_id="MPS-SESSION-1",
    )

    add_file_entry(
        manifest,
        source_path="/card/DSC0001.ARW",
        destination_path=raw,
        action="copied",
        status="verified",
    )

    jpeg.write_bytes(jpeg_content)

    add_file_entry(
        manifest,
        source_path="/card/DSC0001.JPG",
        destination_path=jpeg,
        action="copied",
        status="verified",
    )

    jpeg.unlink()

    write_manifest_to_path(
        manifest,
        root / "import_manifest.json",
    )

    provenance_root = root / "provenance"

    raw_certificate = (
        provenance_root / "RAW-CERT.json"
    )
    jpeg_certificate = (
        provenance_root / "JPEG-CERT.json"
    )

    raw_certificate.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_certificate.write_text(
        "raw certificate",
        encoding="utf-8",
    )
    jpeg_certificate.write_text(
        "jpeg certificate",
        encoding="utf-8",
    )

    raw_event_directory = (
        provenance_root
        / "events"
        / "MPS-PROV-RAW-1"
    )
    jpeg_event_directory = (
        provenance_root
        / "events"
        / "MPS-PROV-JPEG-1"
    )

    raw_event_directory.mkdir(
        parents=True,
    )
    jpeg_event_directory.mkdir(
        parents=True,
    )

    (
        raw_event_directory / "event.json"
    ).write_text(
        "raw event",
        encoding="utf-8",
    )

    (
        jpeg_event_directory / "event.json"
    ).write_text(
        "jpeg event",
        encoding="utf-8",
    )

    write_index(
        ProvenanceCertificateIndex(
            entries=[
                _index_entry(
                    path=raw,
                    provenance_id="MPS-PROV-RAW-1",
                    certificate_path=raw_certificate,
                    sha256=_sha256(raw_content),
                ),
                _index_entry(
                    path=jpeg,
                    provenance_id="MPS-PROV-JPEG-1",
                    certificate_path=jpeg_certificate,
                    sha256=_sha256(jpeg_content),
                ),
            ]
        ),
        index_path(root),
    )

    candidate = MissingImportedJpeg(
        stem="DSC0001",
        jpeg_path=jpeg,
        jpeg_provenance_id="MPS-PROV-JPEG-1",
        jpeg_sha256=_sha256(jpeg_content),
        raw_path=raw,
        raw_provenance_id="MPS-PROV-RAW-1",
        raw_sha256=_sha256(raw_content),
        raw_hash_matches=True,
    )

    return root, candidate


def test_verified_pair_is_removed_from_active_manifest(
    tmp_path: Path,
):
    root, candidate = _build_session(tmp_path)

    result = execute_culling_candidate(
        root,
        candidate,
    )

    assert result.success is True
    assert result.removed_manifest_entries == 2

    manifest = load_manifest(
        root / "import_manifest.json"
    )

    assert manifest.file_count == 0
    assert manifest.total_bytes == 0


def test_verified_pair_is_removed_from_active_index(
    tmp_path: Path,
):
    root, candidate = _build_session(tmp_path)

    result = execute_culling_candidate(
        root,
        candidate,
    )

    assert result.success is True
    assert result.removed_index_entries == 2

    certificate_index = load_index(
        index_path(root)
    )

    assert certificate_index.entries == []


def test_raw_and_provenance_are_quarantined(
    tmp_path: Path,
):
    root, candidate = _build_session(tmp_path)

    result = execute_culling_candidate(
        root,
        candidate,
    )

    assert result.success is True
    assert candidate.raw_path is not None
    assert not candidate.raw_path.exists()

    quarantine = (
        root
        / ".mps_quarantine"
        / "culling"
        / "DSC0001"
    )

    assert (
        quarantine / "DSC0001.ARW"
    ).exists()

    assert (
        quarantine
        / "provenance"
        / "certificates"
        / "RAW-CERT.json"
    ).exists()

    assert (
        quarantine
        / "provenance"
        / "certificates"
        / "JPEG-CERT.json"
    ).exists()

    assert (
        quarantine
        / "provenance"
        / "events"
        / "MPS-PROV-RAW-1"
        / "event.json"
    ).exists()

    assert (
        quarantine
        / "provenance"
        / "events"
        / "MPS-PROV-JPEG-1"
        / "event.json"
    ).exists()


def test_changed_raw_aborts_without_changes(
    tmp_path: Path,
):
    root, candidate = _build_session(tmp_path)

    assert candidate.raw_path is not None
    candidate.raw_path.write_bytes(
        b"changed after analysis"
    )

    result = execute_culling_candidate(
        root,
        candidate,
    )

    assert result.success is False
    assert "RAW hash changed" in result.message
    assert candidate.raw_path.exists()

    manifest = load_manifest(
        root / "import_manifest.json"
    )
    certificate_index = load_index(
        index_path(root)
    )

    assert manifest.file_count == 2
    assert len(certificate_index.entries) == 2
    assert not (
        root / ".mps_quarantine"
    ).exists()


def test_jpeg_reappearing_aborts_without_changes(
    tmp_path: Path,
):
    root, candidate = _build_session(tmp_path)

    candidate.jpeg_path.write_bytes(
        b"jpeg restored"
    )

    result = execute_culling_candidate(
        root,
        candidate,
    )

    assert result.success is False
    assert "JPG exists again" in result.message

    assert candidate.raw_path is not None
    assert candidate.raw_path.exists()

    manifest = load_manifest(
        root / "import_manifest.json"
    )

    assert manifest.file_count == 2
