import json
from pathlib import Path

from mps.services.manifest_writer import file_sha256
from mps.services.post_import_verifier import verify_import_root


def _write_manifest(
    root: Path,
    destination: Path,
    session_id: str = "MPS-SESSION-1",
) -> Path:
    manifest_path = root / "import_manifest.json"

    manifest = {
        "session_id": session_id,
        "files": [
            {
                "destination_path": str(destination),
                "sha256": file_sha256(destination),
            }
        ],
    }

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    return manifest_path


def _write_provenance(
    root: Path,
    destination: Path,
    manifest_path: Path,
    session_id: str = "MPS-SESSION-1",
) -> None:
    provenance = root / "provenance"
    provenance.mkdir()

    sha256 = file_sha256(destination)
    certificate_path = provenance / "MPS-CERT-1.json"

    certificate = {
        "certificate_id": "MPS-CERT-1",
        "session_id": session_id,
        "destination_path": str(destination),
        "sha256": sha256,
        "manifest_path": str(manifest_path),
    }

    certificate_path.write_text(
        json.dumps(certificate),
        encoding="utf-8",
    )

    index = {
        "entries": [
            {
                "certificate_id": "MPS-CERT-1",
                "session_id": session_id,
                "destination_path": str(destination),
                "certificate_path": str(certificate_path),
                "sha256": sha256,
            }
        ]
    }

    (provenance / "certificate_index.json").write_text(
        json.dumps(index),
        encoding="utf-8",
    )


def test_verify_import_root_reports_safe_to_release(tmp_path: Path):
    root = tmp_path / "import"
    root.mkdir()

    raw = root / "DSC0001.ARW"
    raw.write_bytes(b"raw-data")

    manifest_path = _write_manifest(root, raw)
    _write_provenance(root, raw, manifest_path)

    result = verify_import_root(root)

    assert result.expected_files == 1
    assert result.verified_files == 1
    assert result.expected_certificates == 1
    assert result.verified_certificates == 1
    assert result.provenance_errors == []
    assert result.safe_to_release is True
    assert result.card_status == "SAFE TO RELEASE"


def test_verify_import_root_reports_missing_file(tmp_path: Path):
    root = tmp_path / "import"
    root.mkdir()

    missing = root / "DSC0002.ARW"

    manifest = {
        "session_id": "MPS-SESSION-1",
        "files": [
            {
                "destination_path": str(missing),
                "sha256": "0" * 64,
            }
        ],
    }

    (root / "import_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    result = verify_import_root(root)

    assert result.expected_files == 1
    assert result.verified_files == 0
    assert result.missing_files == [missing]
    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"


def test_verify_import_root_blocks_session_id_mismatch(tmp_path: Path):
    root = tmp_path / "import"
    root.mkdir()

    raw = root / "DSC0003.ARW"
    raw.write_bytes(b"raw-data")

    manifest_path = _write_manifest(root, raw)
    _write_provenance(
        root,
        raw,
        manifest_path,
        session_id="WRONG-SESSION",
    )

    result = verify_import_root(root)

    assert result.verified_files == 1
    assert result.verified_certificates == 0
    assert result.provenance_errors
    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"


def test_verify_import_root_blocks_certificate_hash_mismatch(
    tmp_path: Path,
):
    root = tmp_path / "import"
    root.mkdir()

    raw = root / "DSC0004.ARW"
    raw.write_bytes(b"raw-data")

    manifest_path = _write_manifest(root, raw)
    _write_provenance(root, raw, manifest_path)

    certificate_path = root / "provenance" / "MPS-CERT-1.json"
    certificate = json.loads(
        certificate_path.read_text(encoding="utf-8")
    )
    certificate["sha256"] = "0" * 64

    certificate_path.write_text(
        json.dumps(certificate),
        encoding="utf-8",
    )

    result = verify_import_root(root)

    assert result.verified_files == 1
    assert result.verified_certificates == 0
    assert result.provenance_errors
    assert result.safe_to_release is False
    assert result.card_status == "DO NOT RELEASE"
