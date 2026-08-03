from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from mps.models.import_media_session import ImportMediaSession
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.manifest_writer import file_sha256, read_manifest
from mps.services.post_import_verifier import verify_import_root
from mps.services.provenance_event_chain_validator import (
    validate_provenance_event_chain,
)
from mps.services.provenance_event_chain_writer import load_event_chain
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import load_index


@dataclass(frozen=True, slots=True)
class PartialBatchRecovery:
    recovered_sources: tuple[Path, ...] = ()
    reason: str | None = None

    @property
    def recovered(self) -> bool:
        return bool(self.recovered_sources)


def _inside(path: Path, root: Path) -> bool:
    try:
        return path.resolve(strict=False).is_relative_to(
            root.resolve(strict=False)
        )
    except (OSError, RuntimeError):
        return False


def recover_verified_partial_batch_sources(
    session: ImportMediaSession,
    import_root: str | Path,
    *,
    session_id: str,
    protected_state_pending: bool = False,
) -> PartialBatchRecovery:
    """Adopt same-session manifest sources after complete validation.

    Recovery is deliberately all-or-nothing. Any ambiguity leaves the
    session untouched so normal reconciliation can report the mismatch.
    """

    root = Path(import_root)
    destination = session.destination
    if protected_state_pending:
        return PartialBatchRecovery(reason="protected_state_pending")
    if destination is None or destination.import_root != root:
        return PartialBatchRecovery(reason="destination_mismatch")
    if session.session_id != session_id:
        return PartialBatchRecovery(reason="session_id_mismatch")

    manifest_path = root / "import_manifest.json"
    try:
        manifest = read_manifest(manifest_path)
        verification = verify_import_root(root)
        certificate_index = load_index(index_path(root))
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return PartialBatchRecovery(reason="invalid_import_evidence")

    if manifest.get("session_id") != session_id:
        return PartialBatchRecovery(reason="manifest_session_mismatch")
    if not verification.safe_to_release:
        return PartialBatchRecovery(reason="import_root_not_verified")

    entries = list(manifest.get("files", []))
    sources: list[Path] = []
    entries_by_source: dict[Path, dict] = {}
    for entry in entries:
        source_value = entry.get("source_path")
        if not isinstance(source_value, str) or not source_value:
            return PartialBatchRecovery(reason="invalid_source_path")
        source = Path(source_value)
        if source in entries_by_source:
            return PartialBatchRecovery(reason="conflicting_source_entry")
        entries_by_source[source] = entry
        sources.append(source)

    processed = set(session.processed_source_files)
    if not processed.issubset(entries_by_source):
        return PartialBatchRecovery(reason="processed_source_conflict")
    unexpected = sorted(set(sources) - processed)
    if not unexpected:
        return PartialBatchRecovery()

    index_by_destination = {}
    for entry in certificate_index.entries:
        if entry.destination_path in index_by_destination:
            return PartialBatchRecovery(reason="conflicting_index_entry")
        index_by_destination[entry.destination_path] = entry

    for source in unexpected:
        entry = entries_by_source[source]
        destination_value = entry.get("destination_path")
        expected_sha256 = entry.get("sha256")
        if entry.get("status") != "verified":
            return PartialBatchRecovery(reason="manifest_entry_not_verified")
        if not isinstance(destination_value, str) or not destination_value:
            return PartialBatchRecovery(reason="invalid_destination_path")
        if not isinstance(expected_sha256, str) or not expected_sha256:
            return PartialBatchRecovery(reason="invalid_manifest_checksum")

        output = Path(destination_value)
        if not _inside(output, root) or not output.is_file():
            return PartialBatchRecovery(reason="destination_unavailable")
        try:
            if file_sha256(output) != expected_sha256:
                return PartialBatchRecovery(reason="destination_checksum_mismatch")
        except OSError:
            return PartialBatchRecovery(reason="destination_unavailable")

        indexed = index_by_destination.get(destination_value)
        if (
            indexed is None
            or indexed.session_id != session_id
            or indexed.sha256 != expected_sha256
        ):
            return PartialBatchRecovery(reason="invalid_provenance_index")

        certificate_path = Path(indexed.certificate_path)
        if not _inside(certificate_path, root / "provenance"):
            return PartialBatchRecovery(reason="invalid_certificate_path")
        try:
            certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return PartialBatchRecovery(reason="invalid_certificate")
        if (
            certificate.get("certificate_id") != indexed.certificate_id
            or certificate.get("provenance_id") != indexed.provenance_id
            or certificate.get("session_id") != session_id
            or certificate.get("source_path") != str(source)
            or certificate.get("destination_path") != destination_value
            or certificate.get("sha256") != expected_sha256
            or certificate.get("manifest_path") != str(manifest_path)
        ):
            return PartialBatchRecovery(reason="invalid_certificate")

        try:
            chain = load_event_chain(root, indexed.provenance_id)
            chain_validation = validate_provenance_event_chain(chain)
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            return PartialBatchRecovery(reason="invalid_ingest_event")
        ingest_events = [
            event
            for event in chain.ordered_events
            if event.event_type is ProvenanceEventType.INGEST
        ]
        if len(ingest_events) != 1 or not chain_validation.valid:
            return PartialBatchRecovery(reason="invalid_ingest_event")
        ingest = ingest_events[0]
        if (
            ingest.session_id != session_id
            or ingest.input_sha256 != expected_sha256
            or ingest.output_sha256 != expected_sha256
            or ingest.metadata.get("certificate_id") != indexed.certificate_id
            or ingest.metadata.get("source_path") != str(source)
            or ingest.metadata.get("destination_path") != destination_value
            or ingest.metadata.get("manifest_path") != str(manifest_path)
        ):
            return PartialBatchRecovery(reason="invalid_ingest_event")

    session.add_processed_source_files(unexpected)
    return PartialBatchRecovery(recovered_sources=tuple(unexpected))
