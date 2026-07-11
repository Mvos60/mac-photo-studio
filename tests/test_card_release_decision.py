from pathlib import Path

from mps.models.card_release_decision import CardReleaseDecision
from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


def _verification(
    *,
    verified: bool,
) -> PostImportVerification:
    if verified:
        return PostImportVerification(
            import_root=Path("/photos/import"),
            manifest_path=Path(
                "/photos/import/import_manifest.json"
            ),
            expected_files=2,
            verified_files=2,
            expected_certificates=2,
            verified_certificates=2,
        )

    return PostImportVerification(
        import_root=Path("/photos/import"),
        manifest_path=Path(
            "/photos/import/import_manifest.json"
        ),
        expected_files=2,
        verified_files=1,
        expected_certificates=2,
        verified_certificates=1,
        provenance_errors=["Certificate hash mismatch"],
    )


def _reconciliation(
    *,
    reconciled: bool,
) -> SourceCardReconciliation:
    if reconciled:
        return SourceCardReconciliation(
            expected_sources=2,
            reconciled_sources=2,
        )

    return SourceCardReconciliation(
        expected_sources=2,
        reconciled_sources=1,
        missing_from_manifest=[
            Path("/media/raw/DSC0001.ARW"),
        ],
    )


def test_card_release_decision_is_safe_when_both_checks_pass():
    decision = CardReleaseDecision(
        verification=_verification(verified=True),
        reconciliation=_reconciliation(reconciled=True),
    )

    assert decision.safe_to_remove is True
    assert decision.status == "SAFE TO REMOVE CARDS"


def test_card_release_decision_blocks_failed_verification():
    decision = CardReleaseDecision(
        verification=_verification(verified=False),
        reconciliation=_reconciliation(reconciled=True),
    )

    assert decision.safe_to_remove is False
    assert decision.status == "DO NOT REMOVE CARDS"


def test_card_release_decision_blocks_failed_reconciliation():
    decision = CardReleaseDecision(
        verification=_verification(verified=True),
        reconciliation=_reconciliation(reconciled=False),
    )

    assert decision.safe_to_remove is False
    assert decision.status == "DO NOT REMOVE CARDS"


def test_card_release_decision_blocks_when_both_checks_fail():
    decision = CardReleaseDecision(
        verification=_verification(verified=False),
        reconciliation=_reconciliation(reconciled=False),
    )

    assert decision.safe_to_remove is False
    assert decision.status == "DO NOT REMOVE CARDS"
