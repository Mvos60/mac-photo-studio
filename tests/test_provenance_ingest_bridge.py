import json

from mps.models.import_decision import (
    CopyOperation,
    ImportDecision,
)
from mps.services.import_engine import run_import


def test_verified_import_creates_ingest_event(tmp_path):
    source = tmp_path / "card" / "DSC0001.ARW"
    source.parent.mkdir()
    source.write_bytes(b"verified raw photo")

    destination_root = tmp_path / "photos"
    destination = destination_root / "DSC0001.ARW"

    decision = ImportDecision(
        destination=destination_root,
        total_files=1,
        estimated_size_bytes=source.stat().st_size,
        copy_operations=[
            CopyOperation(
                source=source,
                destination=destination,
            )
        ],
        warnings=[],
    )

    result = run_import(
        decision,
        dry_run=False,
        write_provenance=True,
        camera_model="ILCE-7M3",
        project="Adriatic",
        day_session="03_Slovenia",
        session_id="MPS-SESSION-001",
    )

    assert result.copied == 1
    assert result.failed == 0

    index_path = (
        destination_root
        / "provenance"
        / "certificate_index.json"
    )

    index_data = json.loads(
        index_path.read_text(encoding="utf-8")
    )

    provenance_id = index_data["entries"][0]["provenance_id"]

    event_directory = (
        destination_root
        / "provenance"
        / "events"
        / provenance_id
    )

    event_paths = list(
        event_directory.glob("*.json")
    )

    assert len(event_paths) == 1

    event_data = json.loads(
        event_paths[0].read_text(encoding="utf-8")
    )

    assert event_data["provenance_id"] == provenance_id
    assert event_data["session_id"] == "MPS-SESSION-001"
    assert event_data["event_type"] == "ingest"
    assert (
        event_data["input_sha256"]
        == event_data["output_sha256"]
    )
    assert event_data["application"] == "Mac Photo Studio"
    assert (
        event_data["metadata"]["camera_model"]
        == "ILCE-7M3"
    )


def test_ingest_event_links_written_certificate(tmp_path):
    source = tmp_path / "card" / "DSC0002.ARW"
    source.parent.mkdir()
    source.write_bytes(b"second verified raw photo")

    destination_root = tmp_path / "photos"

    decision = ImportDecision(
        destination=destination_root,
        total_files=1,
        estimated_size_bytes=source.stat().st_size,
        copy_operations=[
            CopyOperation(
                source=source,
                destination=(
                    destination_root / "DSC0002.ARW"
                ),
            )
        ],
        warnings=[],
    )

    run_import(
        decision,
        dry_run=False,
        write_provenance=True,
        camera_model="ILCE-7M3",
        session_id="MPS-SESSION-002",
    )

    provenance_root = destination_root / "provenance"

    index_data = json.loads(
        (
            provenance_root / "certificate_index.json"
        ).read_text(encoding="utf-8")
    )

    entry = index_data["entries"][0]

    event_directory = (
        provenance_root
        / "events"
        / entry["provenance_id"]
    )

    event_path = next(
        event_directory.glob("*.json")
    )

    event_data = json.loads(
        event_path.read_text(encoding="utf-8")
    )

    certificate_path = provenance_root / (
        event_data["metadata"]["certificate_id"]
        + ".json"
    )

    assert certificate_path.exists()

    certificate_data = json.loads(
        certificate_path.read_text(encoding="utf-8")
    )

    assert (
        event_data["metadata"]["certificate_id"]
        == certificate_data["certificate_id"]
    )
    assert (
        event_data["provenance_id"]
        == certificate_data["provenance_id"]
    )
    assert (
        event_data["input_sha256"]
        == certificate_data["sha256"]
    )
