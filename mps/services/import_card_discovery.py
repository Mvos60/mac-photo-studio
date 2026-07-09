from __future__ import annotations

from mps.config import Settings
from mps.services.card_scanner import scan_cards
from mps.services.import_card_selector import (
    ImportCardSelection,
    select_import_cards,
)


def discover_import_cards(settings: Settings) -> ImportCardSelection:
    """Scan available media and select the most appropriate RAW/JPEG cards."""
    cards = scan_cards(settings)
    return select_import_cards(cards)
