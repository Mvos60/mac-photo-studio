from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndexEntry,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
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


@dataclass(slots=True, frozen=True)
class _IdentityCandidate:
    entry: ProvenanceCertificateIndexEntry
    path: str
    sha256: str


def _resolution_from_candidate(
    candidate: _IdentityCandidate,
) -> ProvenanceIdentityResolution:
    entry = candidate.entry

    return ProvenanceIdentityResolution(
        resolved=True,
        provenance_id=entry.provenance_id,
        certificate_id=entry.certificate_id,
        session_id=entry.session_id,
        destination_path=candidate.path,
        sha256=candidate.sha256,
        errors=[],
    )


def _identity_candidates(
    *,
    import_root: str | Path,
    entries: list[ProvenanceCertificateIndexEntry],
) -> list[_IdentityCandidate]:
    candidates: list[_IdentityCandidate] = []

    for entry in entries:
        candidates.append(
            _IdentityCandidate(
                entry=entry,
                path=entry.destination_path,
                sha256=entry.sha256,
            )
        )

        chain = load_event_chain(
            import_root,
            entry.provenance_id,
        )

        for event in chain.ordered_events:
            output_path = event.metadata.get("output_path")

            if not output_path or event.output_sha256 is None:
                continue

            candidates.append(
                _IdentityCandidate(
                    entry=entry,
                    path=str(output_path),
                    sha256=event.output_sha256,
                )
            )

    return candidates


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

    candidates = _identity_candidates(
        import_root=import_root,
        entries=certificate_index.entries,
    )

    if photo_path is not None:
        resolved_photo_path = Path(photo_path)

        candidates = [
            candidate
            for candidate in candidates
            if Path(candidate.path) == resolved_photo_path
        ]

    if sha256:
        candidates = [
            candidate
            for candidate in candidates
            if candidate.sha256 == sha256
        ]

    if not candidates:
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "No matching provenance identity found"
            ],
        )

    unique_candidates = {
        (
            candidate.entry.provenance_id,
            candidate.path,
            candidate.sha256,
        ): candidate
        for candidate in candidates
    }

    if len(unique_candidates) > 1:
        return ProvenanceIdentityResolution(
            resolved=False,
            errors=[
                "Multiple matching provenance identities found"
            ],
        )

    return _resolution_from_candidate(
        next(iter(unique_candidates.values()))
    )
