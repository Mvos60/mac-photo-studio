from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.services.extended_photo_provenance import (
    ProvenanceHistory,
    read_provenance_history,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
    verify_managed_photo,
)


@dataclass(slots=True, frozen=True)
class PhotoProvenanceHistory:
    photo_path: Path
    trusted: bool
    events: tuple[ProvenanceEvent, ...] = ()
    verification: PhotoProvenanceVerification | None = None
    history: ProvenanceHistory | None = None
    errors: list[str] = field(default_factory=list)


def read_managed_photo_history(
    *,
    settings: Settings,
    photo_path: str | Path,
) -> PhotoProvenanceHistory:
    verification = verify_managed_photo(
        settings=settings,
        photo_path=photo_path,
    )

    file_verification = verification.verification

    if (
        verification.import_root is None
        or file_verification is None
        or file_verification.identity is None
        or file_verification.identity.provenance_id is None
    ):
        return PhotoProvenanceHistory(
            photo_path=verification.photo_path,
            trusted=verification.trusted,
            verification=verification,
            errors=list(verification.errors),
        )

    history = read_provenance_history(
        import_root=verification.import_root,
        provenance_id=(
            file_verification.identity.provenance_id
        ),
    )

    errors = list(verification.errors)

    for error in history.errors:
        if error not in errors:
            errors.append(error)

    return PhotoProvenanceHistory(
        photo_path=verification.photo_path,
        trusted=verification.trusted and history.valid,
        events=history.events,
        verification=verification,
        history=history,
        errors=errors,
    )
