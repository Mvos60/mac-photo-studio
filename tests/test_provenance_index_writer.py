import json

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.provenance_index_writer import (
    write_index,
)


def test_write_index(tmp_path):
    entry = ProvenanceCertificateIndexEntry(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        destination_path="/photos/test.ARW",
        certificate_path="/photos/provenance/CERT-1.json",
        sha256="abcdef",
        camera_model="Sony A7 III",
        created_at="2026-07-08T12:00:00+00:00",
    )

    index = ProvenanceCertificateIndex(
        entries=[entry],
    )

    output = tmp_path / "index.json"

    written = write_index(
        index,
        output,
    )

    assert written.exists()

    data = json.loads(
        written.read_text(
            encoding="utf-8",
        )
    )

    assert len(data["entries"]) == 1
    assert data["entries"][0]["certificate_id"] == "CERT-1"


def test_load_index_restores_entries(tmp_path):
    from mps.services.provenance_index_writer import load_index

    entry = ProvenanceCertificateIndexEntry(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        destination_path="/photos/test.ARW",
        certificate_path="/photos/provenance/CERT-1.json",
        sha256="abcdef",
        camera_model="Sony A7 III",
        created_at="2026-07-08T12:00:00+00:00",
    )

    path = tmp_path / "index.json"

    write_index(
        ProvenanceCertificateIndex(entries=[entry]),
        path,
    )

    loaded = load_index(path)

    assert len(loaded.entries) == 1
    assert loaded.entries[0].certificate_id == "CERT-1"
    assert loaded.entries[0].provenance_id == "PROV-1"
    assert loaded.entries[0].session_id == "SESSION-1"


def test_load_or_create_index_reuses_existing_index(tmp_path):
    from mps.services.provenance_index_writer import (
        load_or_create_index,
    )

    entry = ProvenanceCertificateIndexEntry(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        destination_path="/photos/test.ARW",
        certificate_path="/photos/provenance/CERT-1.json",
        sha256="abcdef",
        camera_model="Sony A7 III",
        created_at="2026-07-08T12:00:00+00:00",
    )

    path = tmp_path / "index.json"

    write_index(
        ProvenanceCertificateIndex(entries=[entry]),
        path,
    )

    loaded = load_or_create_index(path)

    assert len(loaded.entries) == 1
    assert loaded.entries[0].certificate_id == "CERT-1"


def test_load_or_create_index_returns_empty_index(tmp_path):
    from mps.services.provenance_index_writer import (
        load_or_create_index,
    )

    path = tmp_path / "index.json"

    loaded = load_or_create_index(path)

    assert loaded.entries == []
