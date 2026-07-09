from __future__ import annotations

from mps.services.import_card_selector import ImportCardSelection


def build_card_report(selection: ImportCardSelection) -> str:
    lines: list[str] = []

    lines.append("Searching for photo cards...")
    lines.append("")

    if selection.raw_card is not None:
        lines.append("✓ RAW card")
        lines.append(f"  {selection.raw_card.root}")
        lines.append(f"  RAW files : {selection.raw_card.raw_count}")
        lines.append("")

    if selection.jpeg_card is not None:
        lines.append("✓ JPEG card")
        lines.append(f"  {selection.jpeg_card.root}")
        lines.append(f"  JPEG files: {selection.jpeg_card.jpeg_count}")
        lines.append("")

    if selection.warnings:
        lines.append("Warnings")

        for warning in selection.warnings:
            lines.append(f"  - {warning}")

    return "\n".join(lines)
