import json

import pytest

from mps.services.chain_of_custody import (
    create_provenance_record,
    provenance_filename,
    read_provenance_record,
    write_provenance_record,
)


def test_create_provenance_record_has_stable_identity_fields(tmp_path):
    record = create_provenance_record(
        session_id="session-001",
        source_path=tmp_path / "card" / "DSC0001.ARW",
        destination_path=tmp_path / "Photos_Master" / "DSC0001.ARW",
        sha256="a" * 64,
    )

    assert record.provenance_id.startswith("MPS-PROV-")
    assert record.session_id == "session-001"
    assert record.sha256 == "a" * 64
    assert record.status == "created"


def test_create_provenance_record_keeps_camera_and_media_context(tmp_path):
    record = create_provenance_record(
        session_id="session-002",
        source_path=tmp_path / "DCIM" / "DSC0002.ARW",
        destination_path=tmp_path / "archive" / "DSC0002.ARW",
        sha256="b" * 64,
        camera="Sony A7 III",
        source_media="SD_CARD_01",
    )

    assert record.camera == "Sony A7 III"
    assert record.source_media == "SD_CARD_01"


def test_provenance_record_serializes_to_json_dict(tmp_path):
    record = create_provenance_record(
        session_id="session-003",
        source_path=tmp_path / "source.ARW",
        destination_path=tmp_path / "destination.ARW",
        sha256="c" * 64,
    )

    data = record.to_dict()

    assert data["provenance_id"] == record.provenance_id
    assert data["session_id"] == "session-003"
    assert data["destination_path"].endswith("destination.ARW")


def test_write_and_read_provenance_record_round_trip(tmp_path):
    record = create_provenance_record(
        session_id="session-004",
        source_path=tmp_path / "source.ARW",
        destination_path=tmp_path / "destination.ARW",
        sha256="d" * 64,
        status="verified",
    )
    output = tmp_path / "provenance" / provenance_filename(record)

    written = write_provenance_record(record, output)
    loaded = read_provenance_record(written)

    assert loaded.provenance_id == record.provenance_id
    assert loaded.session_id == record.session_id
    assert loaded.sha256 == record.sha256
    assert loaded.status == "verified"


def test_write_provenance_record_creates_human_readable_json(tmp_path):
    record = create_provenance_record(
        session_id="session-005",
        source_path=tmp_path / "source.ARW",
        destination_path=tmp_path / "destination.ARW",
        sha256="e" * 64,
    )
    output = tmp_path / "record.json"

    write_provenance_record(record, output)
    raw = output.read_text(encoding="utf-8")
    data = json.loads(raw)

    assert raw.endswith("\n")
    assert "\n  \"provenance_id\"" in raw
    assert data["sha256"] == "e" * 64


def test_create_provenance_record_requires_session_id(tmp_path):
    with pytest.raises(ValueError):
        create_provenance_record(
            session_id="",
            source_path=tmp_path / "source.ARW",
            destination_path=tmp_path / "destination.ARW",
            sha256="f" * 64,
        )


def test_create_provenance_record_requires_sha256(tmp_path):
    with pytest.raises(ValueError):
        create_provenance_record(
            session_id="session-006",
            source_path=tmp_path / "source.ARW",
            destination_path=tmp_path / "destination.ARW",
            sha256="",
        )
