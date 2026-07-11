from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mps.models.post_import_verification import PostImportVerification
from mps.services.manifest_writer import read_manifest
from mps.services.provenance_index_paths import index_path
from mps.services.verification_pass import verify_manifest


def _manifest_entries(
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    return list(manifest.get("files", []))


def _manifest_by_destination(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        str(entry["destination_path"]): entry
        for entry in _manifest_entries(manifest)
        if entry.get("destination_path")
    }


def _verify_provenance(
    import_root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[int, int, list[str]]:
    expected = len(_manifest_entries(manifest))
    errors: list[str] = []
    verified = 0

    certificate_index_path = index_path(import_root)

    if not certificate_index_path.exists():
        return expected, 0, ["Certificate index is missing"]

    index = json.loads(
        certificate_index_path.read_text(encoding="utf-8")
    )
    index_entries = list(index.get("entries", []))
    manifest_entries = _manifest_by_destination(manifest)
    manifest_session_id = manifest.get("session_id")

    if len(index_entries) != expected:
        errors.append(
            "Certificate count does not match manifest file count"
        )

    for entry in index_entries:
        destination_path = str(entry.get("destination_path", ""))
        certificate_path_value = entry.get("certificate_path")

        if not certificate_path_value:
            errors.append(
                f"Certificate path missing for {destination_path}"
            )
            continue

        certificate_path = Path(certificate_path_value)

        if not certificate_path.exists():
            errors.append(
                f"Certificate file missing: {certificate_path}"
            )
            continue

        certificate = json.loads(
            certificate_path.read_text(encoding="utf-8")
        )

        manifest_entry = manifest_entries.get(destination_path)

        if manifest_entry is None:
            errors.append(
                f"Certificate destination not found in manifest: "
                f"{destination_path}"
            )
            continue

        certificate_errors = False

        if certificate.get("session_id") != manifest_session_id:
            errors.append(
                f"Session ID mismatch: {destination_path}"
            )
            certificate_errors = True

        if certificate.get("manifest_path") != str(manifest_path):
            errors.append(
                f"Manifest path mismatch: {destination_path}"
            )
            certificate_errors = True

        if certificate.get("sha256") != manifest_entry.get("sha256"):
            errors.append(
                f"Certificate hash mismatch: {destination_path}"
            )
            certificate_errors = True

        if entry.get("session_id") != manifest_session_id:
            errors.append(
                f"Index session ID mismatch: {destination_path}"
            )
            certificate_errors = True

        if entry.get("sha256") != manifest_entry.get("sha256"):
            errors.append(
                f"Index hash mismatch: {destination_path}"
            )
            certificate_errors = True

        if not certificate_errors:
            verified += 1

    return expected, verified, errors


def verify_import_root(
    import_root: str | Path,
) -> PostImportVerification:
    root = Path(import_root)
    manifest_path = root / "import_manifest.json"

    manifest = read_manifest(manifest_path)
    verification = verify_manifest(manifest)

    (
        expected_certificates,
        verified_certificates,
        provenance_errors,
    ) = _verify_provenance(
        root,
        manifest_path,
        manifest,
    )

    return PostImportVerification(
        import_root=root,
        manifest_path=manifest_path,
        expected_files=verification.expected_count,
        verified_files=verification.verified_count,
        missing_files=verification.missing_files,
        checksum_mismatches=verification.checksum_mismatches,
        incomplete_entries=verification.incomplete_entries,
        expected_certificates=expected_certificates,
        verified_certificates=verified_certificates,
        provenance_errors=provenance_errors,
    )
