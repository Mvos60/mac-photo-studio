from __future__ import annotations

from pathlib import Path

from mps.config import Settings
from mps.models.import_media_session import ImportMediaSession
from mps.models.post_import_verification import PostImportVerification
from mps.services.import_media_batch_planner import media_import_destination
from mps.services.manifest_writer import read_manifest
from mps.services.post_import_verifier import verify_import_root


def _configured_photos_root(settings: Settings) -> Path:
    return Path(
        settings.get(
            "paths.photos_root",
            "~/Photos_Master",
        )
    ).expanduser()


def can_resume_import_media_session(
    session: ImportMediaSession,
    import_root: str | Path,
    *,
    settings: Settings,
) -> bool:
    try:
        root = Path(import_root)
    except (TypeError, ValueError):
        return False

    destination = session.destination

    if destination is not None:
        selection = destination.selection
        reconstructed_root = media_import_destination(
            settings,
            year=selection.year,
            project=selection.project,
            day=selection.day_session,
            destination_selection=selection,
        )

        if reconstructed_root != destination.import_root:
            return False

        if root != destination.import_root:
            return False

        try:
            configured_root = _configured_photos_root(
                settings
            ).resolve(strict=False)
            persisted_root = (
                destination.import_root
                .expanduser()
                .resolve(strict=False)
            )
        except (OSError, RuntimeError):
            return False

        if not persisted_root.is_relative_to(
            configured_root
        ):
            return False

    if session.session_id is None:
        return False

    manifest_path = root / "import_manifest.json"

    try:
        if not manifest_path.exists():
            return False

        manifest = read_manifest(manifest_path)
    except (OSError, ValueError):
        return False

    if not isinstance(manifest, dict):
        return False

    manifest_session_id = manifest.get("session_id")

    if not isinstance(manifest_session_id, str):
        return False

    if manifest_session_id != session.session_id:
        return False

    try:
        verification = verify_import_root(root)
    except (KeyError, OSError, ValueError):
        return False

    if not isinstance(
        verification,
        PostImportVerification,
    ):
        return False

    return verification.safe_to_release
