from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.card_release_decision import CardReleaseDecision
from mps.models.import_session_request import ImportSessionRequest
from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_planner import create_import_plan
from mps.services.import_wizard_ui import (
    build_card_release_decision_summary,
    build_import_plan_preview,
    build_import_summary,
    build_post_import_verification_summary,
    build_source_card_reconciliation_summary,
    build_wizard_intro,
)


def test_build_wizard_intro():
    card = CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
        raw_count=10,
        jpeg_count=10,
        heif_count=0,
        video_count=0,
        pair_count=10,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=100,
    )

    selection = ImportCardSelection(
        raw_card=card,
        jpeg_card=card,
        warnings=[],
    )

    output = build_wizard_intro(selection)

    assert "Mac Photo Studio Import Wizard" in output
    assert "RAW card" in output
    assert "JPEG card" in output


def test_build_import_summary():
    request = ImportSessionRequest(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=Path("/media/raw"),
        jpeg_folder=Path("/media/jpeg"),
    )

    output = build_import_summary(request)

    assert "Import Summary" in output
    assert "2026" in output
    assert "Adriatic" in output
    assert "03_Slovenia" in output
    assert "/media/raw" in output
    assert "/media/jpeg" in output


def test_build_import_plan_preview(tmp_path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"
    raw.mkdir()
    jpeg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpeg / "DSC0001.JPG").write_bytes(b"jpeg")

    settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )

    plan = create_import_plan(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpeg,
        settings=settings,
    )

    output = build_import_plan_preview(plan)

    assert "Import Plan Preview" in output
    assert "Pairs       : 1" in output
    assert "RAW only    : 0" in output
    assert "JPEG only   : 0" in output
    assert "Total files : 2" in output


def test_build_post_import_verification_summary():
    result = PostImportVerification(
        import_root=Path("/photos/import"),
        manifest_path=Path("/photos/import/import_manifest.json"),
        expected_files=2,
        verified_files=2,
        expected_certificates=2,
        verified_certificates=2,
    )

    output = build_post_import_verification_summary(result)

    assert "Post-Import Verification" in output
    assert "Files expected       : 2" in output
    assert "Files verified       : 2" in output
    assert "Card status          : SAFE TO RELEASE" in output


def test_build_post_import_verification_summary_shows_errors():
    result = PostImportVerification(
        import_root=Path("/photos/import"),
        manifest_path=Path("/photos/import/import_manifest.json"),
        expected_files=2,
        verified_files=1,
        missing_files=[Path("/photos/import/DSC0001.ARW")],
        checksum_mismatches=[Path("/photos/import/DSC0002.ARW")],
        incomplete_entries=1,
        expected_certificates=2,
        verified_certificates=1,
        provenance_errors=["Certificate hash mismatch"],
    )

    output = build_post_import_verification_summary(result)

    assert "DO NOT RELEASE" in output
    assert "Missing files" in output
    assert "Checksum mismatches" in output
    assert "Incomplete manifest entries: 1" in output
    assert "Provenance errors" in output
    assert "Certificate hash mismatch" in output


def test_build_source_card_reconciliation_summary():
    result = SourceCardReconciliation(
        expected_sources=2,
        reconciled_sources=2,
    )

    output = build_source_card_reconciliation_summary(result)

    assert "Source Card Reconciliation" in output
    assert "Sources expected  : 2" in output
    assert "Sources reconciled: 2" in output
    assert "SOURCE CARDS RECONCILED" in output


def test_build_source_card_reconciliation_summary_shows_errors():
    result = SourceCardReconciliation(
        expected_sources=4,
        reconciled_sources=1,
        missing_from_manifest=[Path("/media/raw/DSC0001.ARW")],
        unexpected_manifest_sources=[Path("/media/old/DSC9999.ARW")],
        unverified_destinations=[Path("/photos/DSC0002.JPG")],
        provenance_failures=[Path("/photos/DSC0003.ARW")],
    )

    output = build_source_card_reconciliation_summary(result)

    assert "SOURCE CARDS NOT RECONCILED" in output
    assert "Missing from manifest" in output
    assert "Unexpected manifest sources" in output
    assert "Unverified destinations" in output
    assert "Provenance failures" in output


def test_build_card_release_decision_summary_safe():
    decision = CardReleaseDecision(
        verification=PostImportVerification(
            import_root=Path("/photos/import"),
            manifest_path=Path("/photos/import/import_manifest.json"),
            expected_files=2,
            verified_files=2,
            expected_certificates=2,
            verified_certificates=2,
        ),
        reconciliation=SourceCardReconciliation(
            expected_sources=2,
            reconciled_sources=2,
        ),
    )

    output = build_card_release_decision_summary(decision)

    assert "Final Card Release Decision" in output
    assert "Post-import verification : PASSED" in output
    assert "Source reconciliation    : PASSED" in output
    assert "FINAL STATUS             : SAFE TO REMOVE CARDS" in output


def test_build_card_release_decision_summary_blocked():
    decision = CardReleaseDecision(
        verification=PostImportVerification(
            import_root=Path("/photos/import"),
            manifest_path=Path("/photos/import/import_manifest.json"),
            expected_files=2,
            verified_files=2,
            expected_certificates=2,
            verified_certificates=2,
        ),
        reconciliation=SourceCardReconciliation(
            expected_sources=2,
            reconciled_sources=1,
            missing_from_manifest=[
                Path("/media/raw/DSC0001.ARW"),
            ],
        ),
    )

    output = build_card_release_decision_summary(decision)

    assert "Post-import verification : PASSED" in output
    assert "Source reconciliation    : FAILED" in output
    assert "FINAL STATUS             : DO NOT REMOVE CARDS" in output
