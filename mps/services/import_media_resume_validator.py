from __future__ import annotations

from pathlib import Path

from mps.models.import_media_session import ImportMediaSession
from mps.services.manifest_writer import read_manifest
from mps.services.post_import_verifier import verify_import_root


def can_resume_import_media_session(
    session: ImportMediaSession,
    import_root: str | Path,
) -> bool:
    root = Path(import_root)
    manifest_path = root / "import_manifest.json"

    if session.session_id is None:
        return False

    if not manifest_path.exists():
        return False

    manifest = read_manifest(manifest_path)

    if manifest.get("session_id") != session.session_id:
        return False

    verification = verify_import_root(root)

    return verification.safe_to_release
