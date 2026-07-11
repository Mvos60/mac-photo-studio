from __future__ import annotations

from dataclasses import dataclass

from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


@dataclass(slots=True, frozen=True)
class ImportMediaSessionReconciliation:
    expected_session_id: str
    manifest_session_id: str | None
    source_reconciliation: SourceCardReconciliation
    verification: PostImportVerification

    @property
    def session_id_matches(self) -> bool:
        return (
            self.manifest_session_id
            == self.expected_session_id
        )

    @property
    def reconciled(self) -> bool:
        return (
            self.session_id_matches
            and self.source_reconciliation.reconciled
            and self.verification.safe_to_release
        )

    @property
    def status(self) -> str:
        if self.reconciled:
            return "IMPORT SESSION RECONCILED"

        return "IMPORT SESSION NOT RECONCILED"
