import json
from pathlib import Path

import pytest

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_destination_selection import ImportDestinationSelection
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)
from mps.services.import_media_batch_processor import process_import_media_batch
from mps.services.import_media_partial_batch_recovery import (
    recover_verified_partial_batch_sources,
)


def _evidence(tmp_path: Path):
    photos_root = tmp_path / "Photos"
    settings = Settings({
        "paths": {"photos_root": str(photos_root)},
        "media": {"raw_extensions": ["ARW"], "jpeg_extensions": ["JPG"]},
    })
    source_root = tmp_path / "card"
    source = source_root / "DCIM" / "100MSDCF" / "PHOTO.JPG"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"verified-photo")
    selection = ImportDestinationSelection(2026, "08-03", "Project")
    import_root = selection.destination_path(photos_root)
    session_id = "MPS-SESSION-RECOVERY"
    imported = ImportMediaSession()
    result = process_import_media_batch(
        ImportMediaSelection(sources=[CardScanResult(
            root=source_root,
            dcim_path=source_root / "DCIM",
            raw_count=0,
            jpeg_count=1,
            heif_count=0,
            video_count=0,
            pair_count=0,
            orphan_raw_count=0,
            orphan_jpeg_count=1,
            other_count=0,
            total_size_bytes=source.stat().st_size,
        )]),
        imported,
        settings,
        year=2026,
        project="Project",
        day="08-03",
        destination_selection=selection,
        session_id=session_id,
    )
    assert result.success
    lagging = ImportMediaSession(
        session_id=session_id,
        destination=ImportMediaSessionDestination(selection, import_root),
    )
    return lagging, source, import_root, session_id


def test_recovers_fully_verified_same_session_source(tmp_path: Path):
    session, source, root, session_id = _evidence(tmp_path)
    result = recover_verified_partial_batch_sources(
        session, root, session_id=session_id
    )
    assert result.recovered_sources == (source,)
    assert session.processed_source_files == [source]


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_session",
        "wrong_destination",
        "unverified",
        "missing_destination",
        "checksum_mismatch",
        "missing_certificate",
        "invalid_certificate",
        "missing_index",
        "invalid_index",
        "missing_event",
        "invalid_event",
        "conflicting_source",
        "processed_source_conflict",
        "random_manifest_entry",
    ],
)
def test_unsafe_evidence_is_not_adopted(tmp_path: Path, mutation: str):
    session, source, root, session_id = _evidence(tmp_path)
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = manifest["files"][0]
    index_path = root / "provenance" / "certificate_index.json"
    index = json.loads(index_path.read_text())
    if mutation == "wrong_session":
        session.session_id = "OTHER"
    elif mutation == "wrong_destination":
        session.destination = ImportMediaSessionDestination(
            session.destination.selection, root / "other"
        )
    elif mutation == "unverified":
        entry["status"] = "failed"
        manifest_path.write_text(json.dumps(manifest))
    elif mutation == "missing_destination":
        Path(entry["destination_path"]).unlink()
    elif mutation == "checksum_mismatch":
        Path(entry["destination_path"]).write_bytes(b"tampered")
    elif mutation == "missing_certificate":
        Path(index["entries"][0]["certificate_path"]).unlink()
    elif mutation == "invalid_certificate":
        certificate_path = Path(index["entries"][0]["certificate_path"])
        certificate = json.loads(certificate_path.read_text())
        certificate["source_path"] = "/unrelated/source.JPG"
        certificate_path.write_text(json.dumps(certificate))
    elif mutation == "missing_index":
        index_path.unlink()
    elif mutation == "invalid_index":
        index["entries"][0]["session_id"] = "OTHER"
        index_path.write_text(json.dumps(index))
    elif mutation == "missing_event":
        event_root = root / "provenance" / "events"
        next(event_root.rglob("*.json")).unlink()
    elif mutation == "invalid_event":
        event_root = root / "provenance" / "events"
        event_path = next(event_root.rglob("*.json"))
        event = json.loads(event_path.read_text())
        event["input_sha256"] = "wrong"
        event_path.write_text(json.dumps(event))
    elif mutation == "conflicting_source":
        manifest["files"].append(dict(entry))
        manifest_path.write_text(json.dumps(manifest))
    elif mutation == "processed_source_conflict":
        session.processed_source_files.append(Path("/unrelated/existing.JPG"))
    elif mutation == "random_manifest_entry":
        manifest["files"].append({
            "source_path": "/unrelated/source.JPG",
            "destination_path": str(root / "unrelated.JPG"),
            "sha256": "unknown",
            "action": "copied",
            "status": "verified",
            "bytes": 1,
        })
        manifest_path.write_text(json.dumps(manifest))

    result = recover_verified_partial_batch_sources(
        session, root, session_id=session_id
    )
    assert not result.recovered
    assert source not in session.processed_source_files


def test_protected_state_prevents_recovery(tmp_path: Path):
    session, _source, root, session_id = _evidence(tmp_path)
    result = recover_verified_partial_batch_sources(
        session,
        root,
        session_id=session_id,
        protected_state_pending=True,
    )
    assert result.reason == "protected_state_pending"
    assert session.processed_source_files == []


def test_safe_to_release_false_prevents_recovery(tmp_path: Path, monkeypatch):
    from types import SimpleNamespace

    session, _source, root, session_id = _evidence(tmp_path)
    monkeypatch.setattr(
        "mps.services.import_media_partial_batch_recovery.verify_import_root",
        lambda path: SimpleNamespace(safe_to_release=False),
    )
    result = recover_verified_partial_batch_sources(
        session, root, session_id=session_id
    )
    assert result.reason == "import_root_not_verified"
    assert session.processed_source_files == []
