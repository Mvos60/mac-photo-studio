from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.services.provenance_event_chain_verifier import (
    StoredProvenanceEventChainVerification,
    verify_stored_event_chain,
)
from mps.services.provenance_identity_resolver import (
    ProvenanceIdentityResolution,
    resolve_provenance_identity,
)
from mps.services.stable_file_hash import stable_file_sha256


@dataclass(slots=True, frozen=True)
class ProvenanceFileVerification:
    trusted: bool
    path: Path
    actual_sha256: str | None = None
    identity: ProvenanceIdentityResolution | None = None
    chain: StoredProvenanceEventChainVerification | None = None
    errors: list[str] = field(default_factory=list)


def verify_provenance_file(
    *,
    import_root: str | Path,
    photo_path: str | Path,
) -> ProvenanceFileVerification:
    path = Path(photo_path).expanduser()

    stable_hash = stable_file_sha256(path)

    if not stable_hash.stable:
        return ProvenanceFileVerification(
            trusted=False,
            path=path,
            errors=list(stable_hash.errors),
        )

    actual_sha256 = stable_hash.sha256

    if actual_sha256 is None:
        return ProvenanceFileVerification(
            trusted=False,
            path=path,
            errors=[
                "Stable file SHA-256 was not produced"
            ],
        )

    identity = resolve_provenance_identity(
        import_root=import_root,
        photo_path=path,
    )

    if not identity.resolved or identity.provenance_id is None:
        return ProvenanceFileVerification(
            trusted=False,
            path=path,
            actual_sha256=actual_sha256,
            identity=identity,
            errors=list(identity.errors),
        )

    chain = verify_stored_event_chain(
        import_root,
        identity.provenance_id,
    )

    errors: list[str] = []

    if identity.sha256 != actual_sha256:
        errors.append(
            "Actual file SHA-256 does not match recorded identity"
        )

    if chain.event_count == 0:
        errors.append(
            "Provenance event chain is empty"
        )

    if not chain.valid:
        errors.extend(chain.errors)

    return ProvenanceFileVerification(
        trusted=not errors,
        path=path,
        actual_sha256=actual_sha256,
        identity=identity,
        chain=chain,
        errors=errors,
    )
