from __future__ import annotations

from mps.models.provenance_certificate import ProvenanceCertificate
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType


def ingest_event_from_certificate(
    certificate: ProvenanceCertificate,
    *,
    application_version: str,
) -> ProvenanceEvent:
    return ProvenanceEvent.create(
        provenance_id=certificate.provenance_id,
        session_id=certificate.session_id,
        event_type=ProvenanceEventType.INGEST,
        input_sha256=certificate.sha256,
        output_sha256=certificate.sha256,
        application="Mac Photo Studio",
        application_version=application_version,
        description="Verified camera media ingest",
        metadata={
            "certificate_id": certificate.certificate_id,
            "source_path": certificate.source_path,
            "destination_path": certificate.destination_path,
            "camera_model": certificate.camera_model,
            "manifest_path": certificate.manifest_path,
        },
    )
