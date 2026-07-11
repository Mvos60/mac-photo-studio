from pathlib import Path

from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


def test_source_card_reconciliation_reports_reconciled():
    result = SourceCardReconciliation(
        expected_sources=42,
        reconciled_sources=42,
    )

    assert result.reconciled is True
    assert result.card_status == "SOURCE CARDS RECONCILED"


def test_source_card_reconciliation_blocks_missing_manifest_source():
    result = SourceCardReconciliation(
        expected_sources=2,
        reconciled_sources=1,
        missing_from_manifest=[
            Path("/media/raw/DCIM/DSC0002.ARW"),
        ],
    )

    assert result.reconciled is False
    assert result.card_status == "SOURCE CARDS NOT RECONCILED"


def test_source_card_reconciliation_blocks_unexpected_manifest_source():
    result = SourceCardReconciliation(
        expected_sources=1,
        reconciled_sources=1,
        unexpected_manifest_sources=[
            Path("/media/raw/DCIM/DSC9999.ARW"),
        ],
    )

    assert result.reconciled is False


def test_source_card_reconciliation_blocks_unverified_destination():
    result = SourceCardReconciliation(
        expected_sources=1,
        reconciled_sources=0,
        unverified_destinations=[
            Path("/photos/DSC0001.ARW"),
        ],
    )

    assert result.reconciled is False


def test_source_card_reconciliation_blocks_provenance_failure():
    result = SourceCardReconciliation(
        expected_sources=1,
        reconciled_sources=0,
        provenance_failures=[
            Path("/photos/DSC0001.ARW"),
        ],
    )

    assert result.reconciled is False
