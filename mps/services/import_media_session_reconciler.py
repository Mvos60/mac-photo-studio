from __future__ import annotations

from pathlib import Path

from mps.models.import_media_session import ImportMediaSession
from mps.models.import_media_session_reconciliation import (
    ImportMediaSessionReconciliation,
)
from mps.services.manifest_writer import read_manifest
from mps.services.post_import_verifier import verify_import_root
from mps.services.source_card_reconciler import reconcile_sources


def reconcile_import_media_session(
    session: ImportMediaSession,
    import_root: str | Path,
    *,
    session_id: str,
) -> ImportMediaSessionReconciliation:
    root = Path(import_root)
    manifest_path = root / "import_manifest.json"

    manifest = read_manifest(manifest_path)

    source_reconciliation = reconcile_sources(
        session.processed_source_files,
        root,
    )

    verification = verify_import_root(root)

    return ImportMediaSessionReconciliation(
        expected_session_id=session_id,
        manifest_session_id=manifest.get("session_id"),
        source_reconciliation=source_reconciliation,
        verification=verification,
    )
