import hashlib

from mps.services.verification_pass import verify_manifest


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_verification_pass_reports_verified_manifest(tmp_path):
    photo = tmp_path / "DSC0001.ARW"
    data = b"original raw data"
    photo.write_bytes(data)

    manifest = {
        "entries": [
            {
                "destination": str(photo),
                "sha256": _sha256(data),
            }
        ]
    }

    result = verify_manifest(manifest)

    assert result.ok is True
    assert result.status == "VERIFIED"
    assert result.expected_count == 1
    assert result.verified_count == 1
    assert result.missing_files == []
    assert result.checksum_mismatches == []


def test_verification_pass_reports_missing_file(tmp_path):
    missing = tmp_path / "missing.ARW"

    manifest = {
        "entries": [
            {
                "destination": str(missing),
                "sha256": _sha256(b"missing data"),
            }
        ]
    }

    result = verify_manifest(manifest)

    assert result.ok is False
    assert result.status == "FAILED"
    assert result.expected_count == 1
    assert result.verified_count == 0
    assert result.missing_files == [missing]


def test_verification_pass_reports_checksum_mismatch(tmp_path):
    photo = tmp_path / "DSC0002.ARW"
    photo.write_bytes(b"changed raw data")

    manifest = {
        "entries": [
            {
                "destination": str(photo),
                "sha256": _sha256(b"original raw data"),
            }
        ]
    }

    result = verify_manifest(manifest)

    assert result.ok is False
    assert result.status == "FAILED"
    assert result.expected_count == 1
    assert result.verified_count == 0
    assert result.checksum_mismatches == [photo]


def test_verification_pass_reports_incomplete_manifest_entry(tmp_path):
    manifest = {
        "entries": [
            {
                "destination": str(tmp_path / "DSC0003.ARW"),
            }
        ]
    }

    result = verify_manifest(manifest)

    assert result.ok is False
    assert result.status == "FAILED"
    assert result.expected_count == 1
    assert result.verified_count == 0
    assert result.incomplete_entries == 1


def test_verification_pass_accepts_files_key_for_manifest_compatibility(tmp_path):
    photo = tmp_path / "DSC0004.ARW"
    data = b"compatible manifest data"
    photo.write_bytes(data)

    manifest = {
        "files": [
            {
                "destination_path": str(photo),
                "checksum": _sha256(data),
            }
        ]
    }

    result = verify_manifest(manifest)

    assert result.ok is True
    assert result.status == "VERIFIED"
    assert result.expected_count == 1
    assert result.verified_count == 1
