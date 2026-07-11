import json
from uuid import UUID

from mps.models.import_manifest import manifest_path
from mps.services.manifest_writer import (
    add_file_entry,
    create_manifest,
    file_sha256,
    read_manifest,
    write_manifest,
    write_manifest_to_path,
)


def test_create_manifest_has_session_id_and_metadata():
    manifest = create_manifest(
        project="Adriatic_2026",
        day_session="01_Germany",
        mps_version="0.2.0-dev",
    )

    UUID(manifest.session_id)
    assert manifest.project == "Adriatic_2026"
    assert manifest.day_session == "01_Germany"
    assert manifest.mps_version == "0.2.0-dev"
    assert manifest.file_count == 0
    assert manifest.total_bytes == 0


def test_create_manifest_accepts_fixed_session_id():
    manifest = create_manifest(
        project="Adriatic_2026",
        day_session="02_Austria",
        mps_version="0.2.0-dev",
        session_id="fixed-session",
    )

    assert manifest.session_id == "fixed-session"


def test_file_sha256_is_deterministic(tmp_path):
    photo = tmp_path / "DSC0001.ARW"
    photo.write_bytes(b"trusted raw bytes")

    first = file_sha256(photo)
    second = file_sha256(photo)

    assert first == second
    assert len(first) == 64


def test_add_file_entry_records_destination_hash_and_size(tmp_path):
    source = tmp_path / "card" / "DSC0001.ARW"
    destination = tmp_path / "library" / "DSC0001.ARW"
    source.parent.mkdir()
    destination.parent.mkdir()
    source.write_bytes(b"source bytes")
    destination.write_bytes(b"copied bytes")

    manifest = create_manifest(
        "Adriatic_2026",
        "01_Germany",
        "0.2.0-dev",
    )
    entry = add_file_entry(
        manifest,
        source,
        destination,
        action="copied",
        status="verified",
    )

    assert manifest.file_count == 1
    assert manifest.total_bytes == len(b"copied bytes")
    assert entry.source_path == str(source)
    assert entry.destination_path == str(destination)
    assert entry.sha256 == file_sha256(destination)
    assert entry.action == "copied"
    assert entry.status == "verified"


def test_write_manifest_creates_manifest_directory(tmp_path):
    manifest = create_manifest(
        "Adriatic_2026",
        "01_Germany",
        "0.2.0-dev",
        session_id="session-001",
    )

    path = write_manifest(manifest, tmp_path)

    assert path == manifest_path(tmp_path, "session-001")
    assert path.exists()
    assert path.parent.name == "manifest"


def test_write_manifest_to_exact_path(tmp_path):
    manifest = create_manifest(
        "Adriatic_2026",
        "01_Germany",
        "0.2.0-dev",
        session_id="session-exact",
    )
    requested_path = tmp_path / "import_manifest.json"

    path = write_manifest_to_path(manifest, requested_path)

    assert path == requested_path
    assert requested_path.exists()

    data = read_manifest(requested_path)

    assert data["session_id"] == "session-exact"


def test_written_manifest_contains_file_statistics(tmp_path):
    source = tmp_path / "card" / "DSC0001.JPG"
    destination = tmp_path / "library" / "DSC0001.JPG"
    source.parent.mkdir()
    destination.parent.mkdir()
    source.write_bytes(b"jpeg source")
    destination.write_bytes(b"jpeg destination")

    manifest = create_manifest(
        "Adriatic_2026",
        "01_Germany",
        "0.2.0-dev",
        session_id="session-002",
    )
    add_file_entry(
        manifest,
        source,
        destination,
        action="copied",
        status="verified",
    )
    path = write_manifest(manifest, tmp_path)

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["session_id"] == "session-002"
    assert data["file_count"] == 1
    assert data["total_bytes"] == len(b"jpeg destination")
    assert data["files"][0]["action"] == "copied"
    assert data["files"][0]["status"] == "verified"


def test_read_manifest_returns_dictionary(tmp_path):
    manifest = create_manifest(
        "Adriatic_2026",
        "03_Slovenia",
        "0.2.0-dev",
        session_id="session-003",
    )
    path = write_manifest(manifest, tmp_path)

    data = read_manifest(path)

    assert data["project"] == "Adriatic_2026"
    assert data["day_session"] == "03_Slovenia"
    assert data["session_id"] == "session-003"


def test_manifest_to_dict_is_json_serializable():
    manifest = create_manifest(
        "Adriatic_2026",
        "04_Croatia",
        "0.2.0-dev",
        session_id="session-004",
    )

    encoded = json.dumps(manifest.to_dict())

    assert "session-004" in encoded


def test_load_manifest_restores_existing_files(tmp_path):
    from mps.services.manifest_writer import load_manifest

    destination = tmp_path / "DSC0001.ARW"
    destination.write_bytes(b"raw-data")

    manifest = create_manifest(
        project="Adriatic",
        day_session="03_Slovenia",
        mps_version="0.2.0-dev",
        session_id="MPS-SESSION-1",
    )

    add_file_entry(
        manifest,
        source_path="/card/DSC0001.ARW",
        destination_path=destination,
        action="copied",
        status="verified",
    )

    path = tmp_path / "import_manifest.json"
    write_manifest_to_path(manifest, path)

    loaded = load_manifest(path)

    assert loaded.session_id == "MPS-SESSION-1"
    assert loaded.project == "Adriatic"
    assert loaded.day_session == "03_Slovenia"
    assert len(loaded.files) == 1
    assert loaded.files[0].source_path == "/card/DSC0001.ARW"


def test_load_or_create_manifest_reuses_same_session(tmp_path):
    from mps.services.manifest_writer import load_or_create_manifest

    path = tmp_path / "import_manifest.json"

    first = load_or_create_manifest(
        path,
        project="Adriatic",
        day_session="03_Slovenia",
        mps_version="0.2.0-dev",
        session_id="MPS-SESSION-1",
    )

    write_manifest_to_path(first, path)

    second = load_or_create_manifest(
        path,
        project="Adriatic",
        day_session="03_Slovenia",
        mps_version="0.2.0-dev",
        session_id="MPS-SESSION-1",
    )

    assert second.session_id == first.session_id
    assert second.created_at == first.created_at


def test_load_or_create_manifest_rejects_different_session(tmp_path):
    import pytest

    from mps.services.manifest_writer import load_or_create_manifest

    path = tmp_path / "import_manifest.json"

    manifest = create_manifest(
        project="Adriatic",
        day_session="03_Slovenia",
        mps_version="0.2.0-dev",
        session_id="MPS-SESSION-1",
    )

    write_manifest_to_path(manifest, path)

    with pytest.raises(
        ValueError,
        match="different import session",
    ):
        load_or_create_manifest(
            path,
            project="Adriatic",
            day_session="03_Slovenia",
            mps_version="0.2.0-dev",
            session_id="MPS-SESSION-2",
        )
