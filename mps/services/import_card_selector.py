from __future__ import annotations

from dataclasses import dataclass

from mps.models.card import CardScanResult


@dataclass(slots=True, frozen=True)
class ImportCardSelection:
    raw_card: CardScanResult | None
    jpeg_card: CardScanResult | None
    warnings: list[str]


def select_import_cards(cards: list[CardScanResult]) -> ImportCardSelection:
    raw_candidates = [
        card
        for card in cards
        if card.raw_count > 0
    ]
    jpeg_candidates = [
        card
        for card in cards
        if card.jpeg_count > 0
    ]

    warnings: list[str] = []

    raw_card = raw_candidates[0] if raw_candidates else None
    jpeg_card = jpeg_candidates[0] if jpeg_candidates else None

    if raw_card is None:
        warnings.append("No RAW card found")

    if jpeg_card is None:
        warnings.append("No JPEG card found")

    if len(raw_candidates) > 1:
        warnings.append(f"Multiple RAW cards found; using {raw_card.root}")

    if len(jpeg_candidates) > 1:
        warnings.append(f"Multiple JPEG cards found; using {jpeg_card.root}")

    return ImportCardSelection(
        raw_card=raw_card,
        jpeg_card=jpeg_card,
        warnings=warnings,
    )
