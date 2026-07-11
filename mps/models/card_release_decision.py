from __future__ import annotations

from dataclasses import dataclass

from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


@dataclass(slots=True, frozen=True)
class CardReleaseDecision:
    verification: PostImportVerification
    reconciliation: SourceCardReconciliation

    @property
    def safe_to_remove(self) -> bool:
        return (
            self.verification.safe_to_release
            and self.reconciliation.reconciled
        )

    @property
    def status(self) -> str:
        if self.safe_to_remove:
            return "SAFE TO REMOVE CARDS"

        return "DO NOT REMOVE CARDS"
