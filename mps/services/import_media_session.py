from __future__ import annotations

from mps.models.import_media_inventory import ImportMediaInventory
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_inventory import classify_import_media
from mps.services.media_source_identity import (
    media_source_fingerprint,
)


def add_media_to_session(
    session: ImportMediaSession,
    selection: ImportMediaSelection,
) -> ImportMediaInventory:
    """Add newly discovered media and classify the full session inventory."""

    for source in selection.sources:
        fingerprint = media_source_fingerprint(source)

        session.add_source(
            source,
            fingerprint,
        )

    return classify_import_media(
        session.selection,
    )
