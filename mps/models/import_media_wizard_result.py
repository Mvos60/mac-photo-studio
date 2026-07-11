from __future__ import annotations

from dataclasses import dataclass

from mps.models.import_media_session import ImportMediaSession
from mps.models.import_media_session_reconciliation import (
    ImportMediaSessionReconciliation,
)


@dataclass(slots=True, frozen=True)
class ImportMediaWizardResult:
    session: ImportMediaSession
    session_id: str
    batches_processed: int
    copied: int
    failed: int
    completed: bool
    reconciliation: ImportMediaSessionReconciliation | None = None

    @property
    def success(self) -> bool:
        return (
            self.completed
            and self.batches_processed > 0
            and self.failed == 0
            and self.reconciliation is not None
            and self.reconciliation.reconciled
        )
