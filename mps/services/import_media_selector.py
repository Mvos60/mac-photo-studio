from __future__ import annotations

from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection


def select_import_media(
    cards: list[CardScanResult],
) -> ImportMediaSelection:
    """Select all currently available photo media sources."""

    sources = [
        card
        for card in cards
        if card.has_photos
    ]

    return ImportMediaSelection(
        sources=sources,
    )
