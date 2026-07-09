from __future__ import annotations

from mps.services.import_card_report import build_card_report
from mps.services.import_card_selector import ImportCardSelection


def build_wizard_intro(selection: ImportCardSelection) -> str:
    return (
        "Mac Photo Studio Import Wizard\n"
        "==============================\n\n"
        + build_card_report(selection)
    )
