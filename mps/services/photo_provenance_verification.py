from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.config import Settings
from mps.services.extended_photo_provenance import (
    ProvenanceFileVerification,
    verify_provenance_file,
)


@dataclass(slots=True, frozen=True)
class PhotoProvenanceVerification:
    photo_path: Path
    trusted: bool
    import_root: Path | None = None
    verification: ProvenanceFileVerification | None = None
    errors: list[str] = field(default_factory=list)


def _managed_photos_root(
    settings: Settings,
) -> Path:
    return Path(
        settings.get(
            "paths.photos_root",
            "~/Photos_Master",
        )
    ).expanduser()


def _find_import_root(
    *,
    photo_path: Path,
    photos_root: Path,
) -> Path | None:
    try:
        photo_path.relative_to(photos_root)
    except ValueError:
        return None

    for directory in (
        photo_path.parent,
        *photo_path.parents,
    ):
        if directory == photos_root.parent:
            break

        certificate_index = (
            directory
            / "provenance"
            / "certificate_index.json"
        )

        if certificate_index.exists():
            return directory

        if directory == photos_root:
            break

    return None


def verify_managed_photo(
    *,
    settings: Settings,
    photo_path: str | Path,
) -> PhotoProvenanceVerification:
    photo = Path(photo_path).expanduser()
    photos_root = _managed_photos_root(settings)

    if not photo.exists():
        return PhotoProvenanceVerification(
            photo_path=photo,
            trusted=False,
            errors=[
                "Photo file does not exist"
            ],
        )

    if not photo.is_file():
        return PhotoProvenanceVerification(
            photo_path=photo,
            trusted=False,
            errors=[
                "Photo path is not a file"
            ],
        )

    import_root = _find_import_root(
        photo_path=photo,
        photos_root=photos_root,
    )

    if import_root is None:
        return PhotoProvenanceVerification(
            photo_path=photo,
            trusted=False,
            errors=[
                "Photo is not inside a managed provenance import"
            ],
        )

    verification = verify_provenance_file(
        import_root=import_root,
        photo_path=photo,
    )

    return PhotoProvenanceVerification(
        photo_path=photo,
        trusted=verification.trusted,
        import_root=import_root,
        verification=verification,
        errors=list(verification.errors),
    )
