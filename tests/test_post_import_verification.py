from pathlib import Path

from mps.models.post_import_verification import PostImportVerification


def test_post_import_verification_reports_safe_to_release():
    result = PostImportVerification(
        import_root=Path("/photos/2026/Adriatic/03_Slovenia"),
        manifest_path=Path(
            "/photos/2026/Adriatic/03_Slovenia/import_manifest.json"
        ),
        expected_files=42,
        verified_files=42,
    )

    assert result.safe_to_release is True
    assert result.card_status == "SAFE TO RELEASE"


def test_post_import_verification_blocks_missing_file():
    missing = Path("/photos/DSC0001.ARW")

    result = PostImportVerification(
        import_root=Path("/photos"),
        manifest_path=Path("/photos/import_manifest.json"),
        expected_files=2,
        verified_files=1,
        missing_files=[missing],
    )

    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"


def test_post_import_verification_blocks_checksum_mismatch():
    mismatch = Path("/photos/DSC0002.JPG")

    result = PostImportVerification(
        import_root=Path("/photos"),
        manifest_path=Path("/photos/import_manifest.json"),
        expected_files=2,
        verified_files=1,
        checksum_mismatches=[mismatch],
    )

    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"


def test_post_import_verification_blocks_incomplete_entry():
    result = PostImportVerification(
        import_root=Path("/photos"),
        manifest_path=Path("/photos/import_manifest.json"),
        expected_files=2,
        verified_files=1,
        incomplete_entries=1,
    )

    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"
