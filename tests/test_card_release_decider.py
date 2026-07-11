from pathlib import Path

from mps.models.card_release_decision import CardReleaseDecision
from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)
from mps.services.card_release_decider import decide_card_release


def test_decide_card_release_combines_safety_results():
    verification = PostImportVerification(
        import_root=Path("/photos/import"),
        manifest_path=Path(
            "/photos/import/import_manifest.json"
        ),
        expected_files=2,
        verified_files=2,
        expected_certificates=2,
        verified_certificates=2,
    )

    reconciliation = SourceCardReconciliation(
        expected_sources=2,
        reconciled_sources=2,
    )

    decision = decide_card_release(
        verification,
        reconciliation,
    )

    assert isinstance(decision, CardReleaseDecision)
    assert decision.verification is verification
    assert decision.reconciliation is reconciliation
    assert decision.safe_to_remove is True
    assert decision.status == "SAFE TO REMOVE CARDS"
