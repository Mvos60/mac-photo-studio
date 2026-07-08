from pathlib import Path

from mps.models.import_session import ImportSession
from mps.services.session_manager import ImportSessionManager


def test_start_session_creates_session_with_identity(tmp_path):
    manager = ImportSessionManager(tmp_path)

    session = manager.start_session(
        camera="Sony A7 III",
        card_label="CARD_A",
        files_discovered=12,
    )

    assert session.session_id
    assert session.status == "started"
    assert session.camera == "Sony A7 III"
    assert session.card_label == "CARD_A"
    assert session.files_discovered == 12
    assert session.started_at
    assert session.ended_at is None


def test_save_session_writes_json_file(tmp_path):
    manager = ImportSessionManager(tmp_path)
    session = manager.start_session(camera="Sony A7 III")

    path = manager.save_session(session)

    assert path.exists()
    assert path.name == f"{session.session_id}.json"
    assert "Sony A7 III" in path.read_text(encoding="utf-8")


def test_load_session_restores_saved_session(tmp_path):
    manager = ImportSessionManager(tmp_path)
    session = manager.start_session(card_label="CARD_B", files_discovered=5)
    manager.save_session(session)

    loaded = manager.load_session(session.session_id)

    assert loaded.session_id == session.session_id
    assert loaded.card_label == "CARD_B"
    assert loaded.files_discovered == 5
    assert loaded.status == "started"


def test_finish_session_records_summary_and_manifest(tmp_path):
    manager = ImportSessionManager(tmp_path)
    session = manager.start_session(files_discovered=10)

    finished = manager.finish_session(
        session,
        files_imported=8,
        files_skipped=2,
        conflicts=0,
        manifest_path=Path("manifests/session.json"),
    )

    assert finished.status == "completed"
    assert finished.ended_at is not None
    assert finished.files_imported == 8
    assert finished.files_skipped == 2
    assert finished.conflicts == 0
    assert finished.manifest_path == "manifests/session.json"


def test_import_session_can_be_finished_directly():
    session = ImportSession()

    session.finish(status="failed")

    assert session.status == "failed"
    assert session.ended_at is not None
