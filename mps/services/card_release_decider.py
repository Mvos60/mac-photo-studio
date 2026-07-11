from __future__ import annotations

from mps.models.card_release_decision import CardReleaseDecision
from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


def decide_card_release(
    verification: PostImportVerification,
    reconciliation: SourceCardReconciliation,
) -> CardReleaseDecision:
    """Build the final card release decision."""

    return CardReleaseDecision(
        verification=verification,
        reconciliation=reconciliation,
    )
