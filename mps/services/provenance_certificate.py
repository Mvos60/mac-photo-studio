from __future__ import annotations

import hashlib
from pathlib import Path

from mps.models.provenance_certificate import PhotoProvenanceCertificate


_CHUNK_SIZE = 65536


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _short(value: str, length: int = 12) -> str:
    return value.replace("-", "")[:length].upper()


def build_certificate_id(session_id: str, sha256: str) -> str:
    return f"MPS-{_short(session_id, 8)}-{sha256[:12].upper()}"


def create_photo_provenance_certificate(
    *,
    provenance_id: str,
    session_id: str,
    source_path: str | Path,
    destination_path: str | Path,
    verification_status: str = "verified",
    camera: str | None = None,
    source_media: str | None = None,
    mps_version: str | None = None,
) -> PhotoProvenanceCertificate:
    destination = Path(destination_path)
    sha256 = _sha256(destination)
    certificate_id = build_certificate_id(session_id, sha256)

    return PhotoProvenanceCertificate(
        certificate_id=certificate_id,
        provenance_id=provenance_id,
        session_id=session_id,
        source_path=str(source_path),
        destination_path=str(destination),
        sha256=sha256,
        verification_status=verification_status,
        camera=camera,
        source_media=source_media,
        mps_version=mps_version,
    )
