from __future__ import annotations

from mps.config import Settings
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.card_scanner import scan_cards
from mps.services.import_media_selector import select_import_media


def discover_import_media(
    settings: Settings,
) -> ImportMediaSelection:
    """Discover all currently available photo media sources."""

    cards = scan_cards(settings)

    return select_import_media(cards)
