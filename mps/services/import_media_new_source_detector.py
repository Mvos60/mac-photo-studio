from __future__ import annotations

from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.media_source_identity import (
    media_source_fingerprint,
)


def detect_new_media_sources(
    session: ImportMediaSession,
    selection: ImportMediaSelection,
) -> ImportMediaSelection:
    """Return currently mounted photo media not yet seen by the session."""

    sources = []

    for source in selection.sources:
        fingerprint = media_source_fingerprint(source)

        if fingerprint in session.source_fingerprints:
            continue

        sources.append(source)

    return ImportMediaSelection(
        sources=sources,
    )
