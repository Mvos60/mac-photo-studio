from pathlib import Path

from mps.models.provenance_certificate import ProvenanceCertificate
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndexEntry,
)


def index_entry_from_certificate(
    certificate: ProvenanceCertificate,
    certificate_path: str | Path,
) -> ProvenanceCertificateIndexEntry:
    return ProvenanceCertificateIndexEntry(
        certificate_id=certificate.certificate_id,
        provenance_id=certificate.provenance_id,
        session_id=certificate.session_id,
        destination_path=certificate.destination_path,
        certificate_path=str(certificate_path),
        sha256=certificate.sha256,
        camera_model=certificate.camera_model,
        created_at=certificate.created_at,
    )
