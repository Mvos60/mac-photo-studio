from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.config import Settings
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
    verify_managed_photo,
)
from mps.services.workflow_application_launcher import (
    WorkflowApplicationLaunch,
    launch_darktable,
)


@dataclass(slots=True, frozen=True)
class DigiKamDarktableHandoff:
    photo_path: Path
    handed_off: bool
    verification: PhotoProvenanceVerification
    launch: WorkflowApplicationLaunch | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)


def handoff_digikam_photo_to_darktable(
    *,
    settings: Settings,
    photo_path: str | Path,
) -> DigiKamDarktableHandoff:
    photo = Path(photo_path).expanduser()

    verification = verify_managed_photo(
        settings=settings,
        photo_path=photo,
    )

    if not verification.trusted:
        return DigiKamDarktableHandoff(
            photo_path=photo,
            handed_off=False,
            verification=verification,
            errors=tuple(verification.errors),
        )

    launch = launch_darktable(
        settings=settings,
        photo_path=photo,
    )

    if not launch.launched:
        return DigiKamDarktableHandoff(
            photo_path=photo,
            handed_off=False,
            verification=verification,
            launch=launch,
            errors=tuple(launch.errors),
        )

    return DigiKamDarktableHandoff(
        photo_path=photo,
        handed_off=True,
        verification=verification,
        launch=launch,
    )
