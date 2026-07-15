import hashlib
from pathlib import Path

from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.culling_analyzer import analyze_culling
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


def test_confirmed_culling_closes_active_pair(
    tmp_path: Path,
):
    root = tmp_path / "Session"
    root.mkdir()

    raw = root / "DSC0001.ARW"
    jpeg = root / "DSC0001.JPG"

    raw_content = b"trusted raw"
    jpeg_content = b"trusted jpeg"

    raw.write_bytes(raw_content)
    jpeg.write_bytes(jpeg_content)

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

    add_file_entry(
        manifest,
        source_path="/card/DSC0001.JPG",
        destination_path=jpeg,
        action="copied",
        status="verified",
    )

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

    for provenance_id in (
        "MPS-PROV-RAW-1",
        "MPS-PROV-JPEG-1",
    ):
        event_directory = (
            provenance_root
            / "events"
            / provenance_id
        )
        event_directory.mkdir(
            parents=True,
        )
        (
            event_directory / "event.json"
        ).write_text(
            "event",
            encoding="utf-8",
        )

    write_index(
        ProvenanceCertificateIndex(
            entries=[
                _entry(
                    path=raw,
                    provenance_id="MPS-PROV-RAW-1",
                    certificate_path=raw_certificate,
                    sha256=_sha256(raw_content),
                ),
                _entry(
                    path=jpeg,
                    provenance_id="MPS-PROV-JPEG-1",
                    certificate_path=jpeg_certificate,
                    sha256=_sha256(jpeg_content),
                ),
            ]
        ),
        index_path(root),
    )

    jpeg.unlink()

    before = analyze_culling(
        root,
        _settings(),
    )

    assert before.missing_jpeg_count == 1
    assert before.orphan_raw_candidate_count == 1

    candidate = before.orphan_raw_candidates[0]

    execution = execute_culling_candidate(
        root,
        candidate,
    )

    assert execution.success is True

    after = analyze_culling(
        root,
        _settings(),
    )

    assert after.missing_jpeg_count == 0
    assert after.orphan_raw_candidate_count == 0

    assert not raw.exists()
    assert not jpeg.exists()

    manifest_after = load_manifest(
        root / "import_manifest.json"
    )
    index_after = load_index(
        index_path(root)
    )

    assert manifest_after.file_count == 0
    assert manifest_after.total_bytes == 0
    assert index_after.entries == []

    quarantine = (
        root
        / ".mps_quarantine"
        / "culling"
        / "DSC0001"
    )

    assert (
        quarantine / "DSC0001.ARW"
    ).exists()
