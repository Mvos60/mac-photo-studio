from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndexEntry,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import load_index


@dataclass(slots=True, frozen=True)
class ProvenanceIdentityResolution:
    resolved: bool
    provenance_id: str | None = None
    certificate_id: str | None = None
    session_id: str | None = None
    destination_path: str | None = None
    sha256: str | None = None
    errors: list[str] = field(default_factory=list)


def _resolution_from_entry(
    entry: ProvenanceCertificateIndexEntry,
) -> ProvenanceIdentityResolution:
    return ProvenanceIdentityResolution(
        resolved=True,
        provenance_id=entry.provenance_id,
        certificate_id=entry.certificate_id,
        session_id=entry.session_id,
        destination_path=entry.destination_path,
        sha256=entry.sha256,
        errors=[],
    )


def resolve_provenance_identity(
    *,
    import_root: str | Path,
    photo_path: str | Path | None = None,
    sha256: str | None = None,
) -> ProvenanceIdentityResolution:
    if photo_path is None and not sha256:
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "photo_path or sha256 is required"
            ],
        )

    certificate_index_path = index_path(import_root)

    if not certificate_index_path.exists():
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "Provenance certificate index does not exist"
            ],
        )

    certificate_index = load_index(
        certificate_index_path
    )

    candidates = list(certificate_index.entries)

    if photo_path is not None:
        resolved_photo_path = Path(photo_path)

        candidates = [
            entry
            for entry in candidates
            if Path(entry.destination_path) == resolved_photo_path
        ]

    if sha256:
        candidates = [
            entry
            for entry in candidates
            if entry.sha256 == sha256
        ]

    if not candidates:
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "No matching provenance identity found"
            ],
        )

    if len(candidates) > 1:
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "Multiple matching provenance identities found"
            ],
        )

    return _resolution_from_entry(
        candidates[0]
    )
