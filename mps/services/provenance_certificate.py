from uuid import uuid4

from mps.models.provenance_certificate import (
    ProvenanceCertificate,
    utc_now_iso,
)


def _new_certificate_id() -> str:
    return f"MPS-CERT-{uuid4()}"


def _new_provenance_id() -> str:
    return f"MPS-PROV-{uuid4()}"


def create_certificate(
    *,
    session_id: str,
    source_path: str,
    destination_path: str,
    sha256: str,
    camera_model: str,
    manifest_path: str,
) -> ProvenanceCertificate:
    return ProvenanceCertificate(
        certificate_id=_new_certificate_id(),
        provenance_id=_new_provenance_id(),
        session_id=session_id,
        source_path=source_path,
        destination_path=destination_path,
        sha256=sha256,
        camera_model=camera_model,
        manifest_path=manifest_path,
        created_at=utc_now_iso(),
    )
