from mps.models.import_session import ImportSession
from mps.services.manifest_writer import file_sha256
from mps.services.resume_engine import build_resume_plan, can_resume, is_incomplete_session


def test_started_session_is_incomplete():
    session = ImportSession(status="started", ended_at=None)

    assert is_incomplete_session(session) is True


def test_completed_session_is_not_resumable():
    session = ImportSession(status="completed", ended_at="2026-07-08T12:00:00+00:00")
    manifest = {"files": []}

    plan = build_resume_plan(session, manifest)

    assert plan.resumable is False
    assert can_resume(plan) is False


def test_resume_plan_detects_verified_existing_file(tmp_path):
    destination = tmp_path / "library" / "DSC0001.ARW"
    destination.parent.mkdir()
    destination.write_bytes(b"verified raw bytes")

    session = ImportSession(session_id="session-001", status="started", ended_at=None)
    manifest = {
        "files": [
            {
                "destination_path": str(destination),
                "sha256": file_sha256(destination),
            }
        ]
    }

    plan = build_resume_plan(session, manifest)

    assert plan.resumable is True
    assert plan.verified_count == 1
    assert plan.remaining_count == 0
    assert plan.conflict_count == 0
    assert can_resume(plan) is True


def test_resume_plan_detects_missing_file(tmp_path):
    destination = tmp_path / "library" / "DSC0002.ARW"

    session = ImportSession(session_id="session-002", status="started", ended_at=None)
    manifest = {
        "files": [
            {
                "destination_path": str(destination),
                "sha256": "0" * 64,
            }
        ]
    }

    plan = build_resume_plan(session, manifest)

    assert plan.resumable is True
    assert plan.verified_count == 0
    assert plan.remaining_count == 1
    assert plan.conflict_count == 0
    assert plan.missing_destinations == [str(destination)]
    assert can_resume(plan) is True


def test_resume_plan_blocks_on_conflicting_existing_file(tmp_path):
    destination = tmp_path / "library" / "DSC0003.ARW"
    destination.parent.mkdir()
    destination.write_bytes(b"changed bytes")

    session = ImportSession(session_id="session-003", status="started", ended_at=None)
    manifest = {
        "files": [
            {
                "destination_path": str(destination),
                "sha256": "1" * 64,
            }
        ]
    }

    plan = build_resume_plan(session, manifest)

    assert plan.resumable is True
    assert plan.verified_count == 0
    assert plan.remaining_count == 0
    assert plan.conflict_count == 1
    assert plan.conflict_destinations == [str(destination)]
    assert can_resume(plan) is False
