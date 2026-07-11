from __future__ import annotations

from dataclasses import dataclass

from mps.models.import_media_batch_plan import ImportMediaBatchPlan
from mps.models.post_import_verification import PostImportVerification


@dataclass(slots=True, frozen=True)
class ImportMediaBatchResult:
    plan: ImportMediaBatchPlan
    copied: int
    failed: int
    verification: PostImportVerification | None
    media_registered: bool

    @property
    def success(self) -> bool:
        return (
            self.failed == 0
            and self.verification is not None
            and self.verification.safe_to_release
            and self.media_registered
        )
