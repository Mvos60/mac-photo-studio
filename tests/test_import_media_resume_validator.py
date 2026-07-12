import json
from pathlib import Path

from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_resume_validator import (
    can_resume_import_media_session,
)


def _write_import_evidence(
    root: Path,
    *,
    session_id: str,
) -> None:
    root.mkdir(parents=True)

    destination = root / "DSC0001.ARW"
    destination.write_bytes(b"raw-data")

    import hashlib

    sha256 = hashlib.sha256(b"raw-data").hexdigest()

    manifest = {
        "session_id": session_id,
        "files": [
            {
                "source_path": "/media/card/DSC0001.ARW",
                "destination_path": str(destination),
                "sha256": sha256,
                "action": "copied",
                "status": "verified",
                "bytes": 8,
            }
        ],
    }

    manifest_path = root / "import_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    provenance = root / "provenance"
    provenance.mkdir()

    certificate_path = provenance / "MPS-CERT-1.json"

    certificate = {
        "session_id": session_id,
        "manifest_path": str(manifest_path),
        "destination_path": str(destination),
        "sha256": sha256,
    }

    certificate_path.write_text(
        json.dumps(certificate),
        encoding="utf-8",
    )

    index = {
        "entries": [
            {
                "session_id": session_id,
                "destination_path": str(destination),
                "certificate_path": str(certificate_path),
                "sha256": sha256,
            }
        ]
    }

    (
        provenance / "certificate_index.json"
    ).write_text(
        json.dumps(index),
        encoding="utf-8",
    )


def test_verified_same_session_can_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
    ) is True


def test_session_id_mismatch_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-OTHER",
    )

    assert can_resume_import_media_session(
        session,
        root,
    ) is False


def test_missing_session_id_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession()

    assert can_resume_import_media_session(
        session,
        root,
    ) is False


def test_tampered_destination_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    (root / "DSC0001.ARW").write_bytes(
        b"tampered"
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
    ) is False
