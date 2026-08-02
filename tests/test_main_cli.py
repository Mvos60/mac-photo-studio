import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mps.config import Settings
from mps.main import main
from mps.models.import_session_request import ImportSessionRequest
from mps.models.post_import_verification import PostImportVerification
from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


def test_cli_plan_import_uses_year_first_layout(
    tmp_path,
    monkeypatch,
    capsys,
):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )

    exit_code = main(
        [
            "--plan-import",
            "2026",
            "Adriatic",
            "03_Slovenia",
            str(raw),
            str(jpg),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Year:         2026" in output
    assert "Project:      Adriatic" in output
    assert "03_Slovenia" in output
    assert str(
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    ) in output


def test_cli_real_import_copies_files_and_reconciles_sources(
    tmp_path,
    monkeypatch,
    capsys,
):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw-data")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg-data")

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.identify_camera_model",
        lambda path: "ILCE-7M3",
    )

    exit_code = main(
        [
            "--import",
            "2026",
            "Adriatic",
            "03_Slovenia",
            str(raw),
            str(jpg),
        ]
    )

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )
    provenance_dir = destination / "provenance"
    index_file = provenance_dir / "certificate_index.json"
    manifest_file = destination / "import_manifest.json"

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio Import" in output
    assert "Camera:       ILCE-7M3" in output
    assert "Success:      True" in output
    assert "Post-Import Verification" in output
    assert "Card status          : SAFE TO RELEASE" in output
    assert "Source Card Reconciliation" in output
    assert "Sources expected  : 2" in output
    assert "Sources reconciled: 2" in output
    assert "Card status       : SOURCE CARDS RECONCILED" in output

    assert (destination / "DSC0001.ARW").read_bytes() == b"raw-data"
    assert (destination / "DSC0001.JPG").read_bytes() == b"jpg-data"
    assert (destination / "mps_import.log").exists()

    assert manifest_file.exists()
    assert provenance_dir.exists()
    assert index_file.exists()
    assert len(list(provenance_dir.glob("MPS-CERT-*.json"))) == 2

    manifest = json.loads(
        manifest_file.read_text(encoding="utf-8")
    )

    assert manifest["project"] == "Adriatic"
    assert manifest["day_session"] == "03_Slovenia"
    assert manifest["file_count"] == 2


def test_cli_real_import_blocks_release_when_verification_fails(
    tmp_path,
    monkeypatch,
    capsys,
):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw-data")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg-data")

    reconciliation_called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.identify_camera_model",
        lambda path: "ILCE-7M3",
    )
    monkeypatch.setattr(
        "mps.main.verify_import_root",
        lambda root: PostImportVerification(
            import_root=Path(root),
            manifest_path=Path(root) / "import_manifest.json",
            expected_files=2,
            verified_files=1,
            expected_certificates=2,
            verified_certificates=1,
            provenance_errors=["Certificate hash mismatch"],
        ),
    )
    monkeypatch.setattr(
        "mps.main.reconcile_source_cards",
        lambda plan: reconciliation_called.append(plan),
    )

    exit_code = main(
        [
            "--import",
            "2026",
            "Adriatic",
            "03_Slovenia",
            str(raw),
            str(jpg),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Card status          : DO NOT RELEASE" in output
    assert "Certificate hash mismatch" in output
    assert "Source Card Reconciliation" not in output
    assert reconciliation_called == []


def test_cli_real_import_blocks_unreconciled_sources(
    tmp_path,
    monkeypatch,
    capsys,
):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw-data")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg-data")

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.identify_camera_model",
        lambda path: "ILCE-7M3",
    )
    monkeypatch.setattr(
        "mps.main.reconcile_source_cards",
        lambda plan: SourceCardReconciliation(
            expected_sources=2,
            reconciled_sources=1,
            missing_from_manifest=[
                Path("/media/raw/DSC0001.ARW"),
            ],
        ),
    )

    exit_code = main(
        [
            "--import",
            "2026",
            "Adriatic",
            "03_Slovenia",
            str(raw),
            str(jpg),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Post-Import Verification" in output
    assert "Card status          : SAFE TO RELEASE" in output
    assert "Source Card Reconciliation" in output
    assert "SOURCE CARDS NOT RECONCILED" in output
    assert "Missing from manifest" in output


def test_cli_import_command_cancel_does_not_start_media_session(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: called.append(
            (args, kwargs)
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n",
    )

    exit_code = main(["import"])

    assert exit_code == 0
    assert called == []


def test_cli_import_command_runs_media_session(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.models.import_media_wizard_result import (
        ImportMediaWizardResult,
    )
    from mps.services.import_progress_output import (
        print_import_progress,
    )

    called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )

    def run_session(settings, **kwargs):
        from mps.models.import_media_session_reconciliation import (
            ImportMediaSessionReconciliation,
        )
        from mps.models.post_import_verification import (
            PostImportVerification,
        )
        from mps.models.source_card_reconciliation import (
            SourceCardReconciliation,
        )

        called.append(kwargs)

        reconciliation = ImportMediaSessionReconciliation(
            expected_session_id="MPS-SESSION-TEST",
            manifest_session_id="MPS-SESSION-TEST",
            source_reconciliation=SourceCardReconciliation(
                expected_sources=4,
                reconciled_sources=4,
            ),
            verification=PostImportVerification(
                import_root=tmp_path / "Photos_Master",
                manifest_path=(
                    tmp_path
                    / "Photos_Master"
                    / "import_manifest.json"
                ),
                expected_files=4,
                verified_files=4,
                expected_certificates=4,
                verified_certificates=4,
            ),
        )

        return ImportMediaWizardResult(
            session=ImportMediaSession(),
            session_id="MPS-SESSION-TEST",
            batches_processed=2,
            copied=4,
            failed=0,
            completed=True,
            reconciliation=reconciliation,
        )

    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        run_session,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    exit_code = main(["import"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert called == [
        {
            "year": 2026,
            "project": "Adriatic",
            "day": "03_Slovenia",
            "session": None,
            "session_state_path": (
                tmp_path
                / "state"
                / "active_import_session.json"
            ),
            "progress_callback": print_import_progress,
        }
    ]
    assert "Year        : 2026" in output
    assert "Project     : Adriatic" in output
    assert "Day/session : 03_Slovenia" in output
    assert "Import Session Summary" in output
    assert "Batches processed : 2" in output
    assert "Files copied      : 4" in output
    assert "Success           : True" in output


def test_cli_import_resumes_verified_saved_session(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.models.import_media_wizard_result import (
        ImportMediaWizardResult,
    )
    from mps.services.import_media_session_store import (
        save_import_media_session,
    )

    state_dir = tmp_path / "state"
    state_path = (
        state_dir / "active_import_session.json"
    )

    saved = ImportMediaSession(
        session_id="MPS-SESSION-RESUME",
        source_fingerprints={"raw-card"},
        processed_source_files=[
            Path("/media/card/DSC0001.ARW")
        ],
    )

    save_import_media_session(saved, state_path)

    called = []

    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        state_dir,
    )
    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.can_resume_import_media_session",
        lambda session, root: True,
    )

    def run_session(settings, **kwargs):
        called.append(kwargs)

        return ImportMediaWizardResult(
            session=kwargs["session"],
            session_id="MPS-SESSION-RESUME",
            batches_processed=1,
            copied=1,
            failed=0,
            completed=False,
        )

    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        run_session,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    exit_code = main(["import"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert called[0]["session"].session_id == (
        "MPS-SESSION-RESUME"
    )
    assert called[0]["session_state_path"] == state_path
    assert "Resuming verified import session." in output


def test_cli_import_blocks_unsafe_saved_session(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.services.import_media_session_store import (
        save_import_media_session,
    )

    state_dir = tmp_path / "state"
    state_path = (
        state_dir / "active_import_session.json"
    )

    save_import_media_session(
        ImportMediaSession(
            session_id="MPS-SESSION-BAD",
        ),
        state_path,
    )

    called = []

    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        state_dir,
    )
    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.can_resume_import_media_session",
        lambda session, root: False,
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: called.append(
            (args, kwargs)
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    exit_code = main(["import"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert called == []
    assert (
        "Saved import session cannot be resumed safely."
        in output
    )
    assert state_path.exists()


def test_cli_verify_photo_reports_trusted(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_verification import (
        PhotoProvenanceVerification,
    )
    from mps.services.provenance_event_chain_verifier import (
        StoredProvenanceEventChainVerification,
    )
    from mps.services.provenance_file_verifier import (
        ProvenanceFileVerification,
    )

    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.verify_managed_photo",
        lambda *, settings, photo_path: (
            PhotoProvenanceVerification(
                photo_path=Path(photo_path),
                trusted=True,
                import_root=tmp_path / "import",
                verification=ProvenanceFileVerification(
                    trusted=True,
                    path=Path(photo_path),
                    actual_sha256="abc123",
                    chain=(
                        StoredProvenanceEventChainVerification(
                            provenance_id="MPS-PROV-001",
                            valid=True,
                            event_count=3,
                        )
                    ),
                ),
            )
        ),
    )

    exit_code = main(
        [
            "verify-photo",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio Photo Verification" in output
    assert "Status:        TRUSTED" in output
    assert "valid recorded photographic lineage" in output
    assert "Events:        3" in output


def test_cli_verify_photo_reports_not_trusted(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_verification import (
        PhotoProvenanceVerification,
    )

    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.verify_managed_photo",
        lambda *, settings, photo_path: (
            PhotoProvenanceVerification(
                photo_path=Path(photo_path),
                trusted=False,
                errors=[
                    "Actual file SHA-256 does not match "
                    "recorded identity"
                ],
            )
        ),
    )

    exit_code = main(
        [
            "verify-photo",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Status:        NOT TRUSTED" in output
    assert (
        "Actual file SHA-256 does not match recorded identity"
        in output
    )


def test_cli_photo_history_prints_readable_events(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.provenance_event import ProvenanceEvent
    from mps.models.provenance_event_type import ProvenanceEventType
    from mps.services.photo_provenance_history import (
        PhotoProvenanceHistory,
    )

    photo = tmp_path / "DSC0001_master.tif"

    events = (
        ProvenanceEvent(
            event_id="MPS-EVENT-001",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-001",
            event_type=ProvenanceEventType.INGEST,
            created_at="2020-01-01T10:00:00Z",
            input_sha256="raw-hash",
            output_sha256="raw-hash",
            application="Mac Photo Studio",
            description="Verified camera media ingest",
            metadata={
                "camera_model": "ILCE-7M3",
            },
        ),
        ProvenanceEvent(
            event_id="MPS-EVENT-002",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-002",
            event_type=ProvenanceEventType.EDIT,
            created_at="2020-01-01T11:00:00Z",
            input_sha256="raw-hash",
            output_sha256="master-hash",
            application="darktable",
            application_version="5.6.0",
            description="RAW development",
            metadata={
                "output_path": str(photo),
            },
        ),
    )

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.read_managed_photo_history",
        lambda *, settings, photo_path: (
            PhotoProvenanceHistory(
                photo_path=Path(photo_path),
                trusted=True,
                events=events,
            )
        ),
    )

    exit_code = main(
        [
            "photo-history",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Photo Provenance History" in output
    assert "Status:        TRUSTED" in output
    assert "1. INGEST" in output
    assert "Camera:      ILCE-7M3" in output
    assert "2. EDIT" in output
    assert "Application: darktable 5.6.0" in output
    assert "RAW development" in output


def test_cli_photo_history_reports_untrusted_history(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_history import (
        PhotoProvenanceHistory,
    )

    photo = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.read_managed_photo_history",
        lambda *, settings, photo_path: (
            PhotoProvenanceHistory(
                photo_path=Path(photo_path),
                trusted=False,
                errors=[
                    "Actual file SHA-256 does not match "
                    "recorded identity"
                ],
            )
        ),
    )

    exit_code = main(
        [
            "photo-history",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Status:        NOT TRUSTED" in output
    assert (
        "Actual file SHA-256 does not match recorded identity"
        in output
    )


def test_cli_record_edit_reports_recorded(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.provenance_event import ProvenanceEvent
    from mps.models.provenance_event_type import ProvenanceEventType
    from mps.services.photo_provenance_recording import (
        PhotoProvenanceRecording,
    )

    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_photo_workflow_action",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=True,
            session_id="MPS-SESSION-TEST",
            event=ProvenanceEvent(
                event_id="MPS-EVENT-001",
                provenance_id="MPS-PROV-001",
                session_id="MPS-SESSION-TEST",
                event_type=ProvenanceEventType.EDIT,
                created_at="2026-07-13T10:00:00Z",
                input_sha256="raw-hash",
                output_sha256="master-hash",
            ),
        ),
    )

    exit_code = main(
        [
            "record-edit",
            str(source),
            str(output),
        ]
    )

    output_text = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio Record Edit" in output_text
    assert "Status:        RECORDED" in output_text
    assert "Event:         EDIT" in output_text
    assert "continues the recorded photographic lineage" in output_text


def test_cli_record_export_reports_recorded(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.provenance_event import ProvenanceEvent
    from mps.models.provenance_event_type import ProvenanceEventType
    from mps.services.photo_provenance_recording import (
        PhotoProvenanceRecording,
    )

    source = tmp_path / "DSC0001_master.tif"
    output = tmp_path / "DSC0001_web.jpg"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_photo_workflow_action",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=True,
            session_id="MPS-SESSION-TEST",
            event=ProvenanceEvent(
                event_id="MPS-EVENT-002",
                provenance_id="MPS-PROV-001",
                session_id="MPS-SESSION-TEST",
                event_type=ProvenanceEventType.EXPORT,
                created_at="2026-07-13T11:00:00Z",
                input_sha256="master-hash",
                output_sha256="jpeg-hash",
            ),
        ),
    )

    exit_code = main(
        [
            "record-export",
            str(source),
            str(output),
        ]
    )

    output_text = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio Record Export" in output_text
    assert "Status:        RECORDED" in output_text
    assert "Event:         EXPORT" in output_text


def test_cli_record_action_reports_failure(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_recording import (
        PhotoProvenanceRecording,
    )

    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_photo_workflow_action",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=False,
            errors=[
                "Source file is not the current provenance chain tip"
            ],
        ),
    )

    exit_code = main(
        [
            "record-edit",
            str(source),
            str(output),
        ]
    )

    output_text = capsys.readouterr().out

    assert exit_code == 1
    assert "Status:        NOT RECORDED" in output_text
    assert (
        "Source file is not the current provenance chain tip"
        in output_text
    )


def test_cli_darktable_edit_uses_darktable_command(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_recording import (
        PhotoProvenanceRecording,
    )

    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_darktable_workflow_command",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=True,
        ),
    )

    exit_code = main(
        [
            "darktable-edit",
            str(source),
            str(output),
        ]
    )

    text = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio darktable Edit" in text
    assert "Status:        RECORDED" in text


def test_cli_digikam_export_uses_digikam_command(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.digikam_workflow_adapter import (
        DigiKamWorkflowResult,
    )

    source = tmp_path / "DSC0001.JPG"
    output = tmp_path / "DSC0001_export.JPG"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_digikam_workflow_command",
        lambda **kwargs: DigiKamWorkflowResult(
            action="export",
            provenance_relevant=True,
            recorded=True,
        ),
    )

    exit_code = main(
        [
            "digikam-export",
            str(source),
            str(output),
        ]
    )

    text = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio digikam Export" in text
    assert "Status:        RECORDED" in text


def test_cli_application_workflow_reports_failure(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.photo_provenance_recording import (
        PhotoProvenanceRecording,
    )

    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.record_darktable_workflow_command",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=False,
            errors=[
                "Source file is not the current provenance chain tip"
            ],
        ),
    )

    exit_code = main(
        [
            "darktable-edit",
            str(source),
            str(output),
        ]
    )

    text = capsys.readouterr().out

    assert exit_code == 1
    assert "Status:        NOT RECORDED" in text
    assert (
        "Source file is not the current provenance chain tip"
        in text
    )


def test_cli_import_launches_digikam_when_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.models.import_media_wizard_result import (
        ImportMediaWizardResult,
    )
    from mps.services.workflow_application_launcher import (
        WorkflowApplicationLaunch,
    )

    settings = _settings(tmp_path)
    settings.data["gui"] = {
        "launch_digikam_after_import": True,
    }

    import_root = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: ImportMediaWizardResult(
            session=ImportMediaSession(),
            session_id="MPS-SESSION-TEST",
            batches_processed=1,
            copied=2,
            failed=0,
            completed=True,
            reconciliation=type(
                "Reconciliation",
                (),
                {"reconciled": True},
            )(),
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    called = []

    monkeypatch.setattr(
        "mps.main.launch_digikam",
        lambda **kwargs: called.append(kwargs)
        or WorkflowApplicationLaunch(
            application="digiKam",
            launched=True,
            target=Path(kwargs["import_root"]),
        ),
    )

    exit_code = main(["import"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert called == [
        {
            "settings": settings,
            "import_root": import_root,
        }
    ]
    assert "digiKam Handoff" in output
    assert "Status           : LAUNCHED" in output


def test_cli_import_skips_digikam_when_disabled(
    tmp_path,
    monkeypatch,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.models.import_media_wizard_result import (
        ImportMediaWizardResult,
    )

    settings = _settings(tmp_path)
    settings.data["gui"] = {
        "launch_digikam_after_import": False,
    }

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: ImportMediaWizardResult(
            session=ImportMediaSession(),
            session_id="MPS-SESSION-TEST",
            batches_processed=1,
            copied=2,
            failed=0,
            completed=True,
            reconciliation=type(
                "Reconciliation",
                (),
                {"reconciled": True},
            )(),
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    called = []

    monkeypatch.setattr(
        "mps.main.launch_digikam",
        lambda **kwargs: called.append(kwargs),
    )

    exit_code = main(["import"])

    assert exit_code == 0
    assert called == []


def test_cli_import_reports_digikam_launch_failure(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.models.import_media_wizard_result import (
        ImportMediaWizardResult,
    )
    from mps.services.workflow_application_launcher import (
        WorkflowApplicationLaunch,
    )

    settings = _settings(tmp_path)
    settings.data["gui"] = {
        "launch_digikam_after_import": True,
    }

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Adriatic",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "03_Slovenia",
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: ImportMediaWizardResult(
            session=ImportMediaSession(),
            session_id="MPS-SESSION-TEST",
            batches_processed=1,
            copied=2,
            failed=0,
            completed=True,
            reconciliation=type(
                "Reconciliation",
                (),
                {"reconciled": True},
            )(),
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )
    monkeypatch.setattr(
        "mps.main.launch_digikam",
        lambda **kwargs: WorkflowApplicationLaunch(
            application="digiKam",
            launched=False,
            target=tmp_path,
            errors=(
                "digiKam application was not found",
            ),
        ),
    )

    exit_code = main(["import"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Status           : NOT LAUNCHED" in output
    assert "digiKam application was not found" in output
def test_cli_analyze_culling_prints_read_only_report(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.culling_analyzer import (
        CullingAnalysis,
        MissingImportedJpeg,
    )

    import_root = tmp_path / "Session"
    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"raw")

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.analyze_culling",
        lambda root, settings: CullingAnalysis(
            import_root=Path(root),
            missing_jpegs=[
                MissingImportedJpeg(
                    stem="DSC0001",
                    jpeg_path=jpeg,
                    jpeg_provenance_id=(
                        "MPS-PROV-JPEG-1"
                    ),
                    jpeg_sha256="jpeg-hash",
                    raw_path=raw,
                    raw_provenance_id=(
                        "MPS-PROV-RAW-1"
                    ),
                    raw_sha256="raw-hash",
                    raw_hash_matches=True,
                ),
            ],
        ),
    )

    exit_code = main(
        [
            "--analyze-culling",
            str(import_root),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Culling Analysis" in output
    assert "Missing imported JPGs          : 1" in output
    assert "Verified orphan RAWs           : 1" in output
    assert "Provenance cleanup candidates  : 0" in output
    assert "DSC0001" in output
    assert "CULL CANDIDATE" in output
    assert (
        "Read-only analysis. No files were changed."
        in output
    )


def test_cli_analyze_culling_passes_settings_to_analyzer(
    tmp_path,
    monkeypatch,
):
    from mps.services.culling_analyzer import (
        CullingAnalysis,
    )

    settings = _settings(tmp_path)
    import_root = tmp_path / "Session"
    called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )

    def analyze(root, received_settings):
        called.append(
            (
                root,
                received_settings,
            )
        )

        return CullingAnalysis(
            import_root=Path(root),
            missing_jpegs=[],
        )

    monkeypatch.setattr(
        "mps.main.analyze_culling",
        analyze,
    )

    exit_code = main(
        [
            "--analyze-culling",
            str(import_root),
        ]
    )

    assert exit_code == 0
    assert called == [
        (
            import_root,
            settings,
        )
    ]


def test_cli_help_lists_analyze_culling(
    capsys,
):
    exit_code = main([])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert (
        "mac-photo-studio --analyze-culling "
        "<import-session-folder>"
        in output
    )


def test_cli_confirm_culling_requires_exact_confirmation(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.culling_analyzer import (
        CullingAnalysis,
        MissingImportedJpeg,
    )

    import_root = tmp_path / "Session"
    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"raw")

    candidate = MissingImportedJpeg(
        stem="DSC0001",
        jpeg_path=jpeg,
        jpeg_provenance_id="MPS-PROV-JPEG-1",
        jpeg_sha256="jpeg-hash",
        raw_path=raw,
        raw_provenance_id="MPS-PROV-RAW-1",
        raw_sha256="raw-hash",
        raw_hash_matches=True,
    )

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.analyze_culling",
        lambda root, settings: CullingAnalysis(
            import_root=Path(root),
            missing_jpegs=[candidate],
        ),
    )

    called = []

    monkeypatch.setattr(
        "mps.main.execute_culling_candidate",
        lambda root, item: called.append(
            (root, item)
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "no",
    )

    exit_code = main(
        [
            "--confirm-culling",
            str(import_root),
            "DSC0001",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert called == []
    assert "Culling cancelled" in output


def test_cli_confirm_culling_executes_verified_candidate(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.culling_analyzer import (
        CullingAnalysis,
        MissingImportedJpeg,
    )
    from mps.services.culling_executor import (
        CullingExecutionResult,
    )

    import_root = tmp_path / "Session"
    raw = import_root / "DSC0001.ARW"
    jpeg = import_root / "DSC0001.JPG"

    import_root.mkdir()
    raw.write_bytes(b"raw")

    candidate = MissingImportedJpeg(
        stem="DSC0001",
        jpeg_path=jpeg,
        jpeg_provenance_id="MPS-PROV-JPEG-1",
        jpeg_sha256="jpeg-hash",
        raw_path=raw,
        raw_provenance_id="MPS-PROV-RAW-1",
        raw_sha256="raw-hash",
        raw_hash_matches=True,
    )

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.analyze_culling",
        lambda root, settings: CullingAnalysis(
            import_root=Path(root),
            missing_jpegs=[candidate],
        ),
    )

    called = []

    def execute(root, item):
        called.append((root, item))

        return CullingExecutionResult(
            success=True,
            stem=item.stem,
            raw_quarantine_path=(
                Path(root)
                / ".mps_quarantine"
                / "culling"
                / item.stem
                / "DSC0001.ARW"
            ),
            removed_manifest_entries=2,
            removed_index_entries=2,
            quarantined_provenance_items=4,
            message=(
                "Culling candidate quarantined successfully"
            ),
        )

    monkeypatch.setattr(
        "mps.main.execute_culling_candidate",
        execute,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "CULL",
    )

    exit_code = main(
        [
            "--confirm-culling",
            str(import_root),
            "DSC0001",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert called == [
        (
            import_root,
            candidate,
        )
    ]
    assert "Status                      : QUARANTINED" in output
    assert "Manifest entries removed    : 2" in output
    assert "Certificate entries removed : 2" in output


def test_cli_confirm_culling_rejects_unknown_candidate(
    tmp_path,
    monkeypatch,
    capsys,
):
    from mps.services.culling_analyzer import (
        CullingAnalysis,
    )

    import_root = tmp_path / "Session"

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.analyze_culling",
        lambda root, settings: CullingAnalysis(
            import_root=Path(root),
            missing_jpegs=[],
        ),
    )

    exit_code = main(
        [
            "--confirm-culling",
            str(import_root),
            "UNKNOWN",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "NOT AN ACTIONABLE CULLING ITEM" in output
    assert "No files were changed." in output


def test_cli_structured_destination_skips_prompts_and_forwards_selection(
    tmp_path,
    monkeypatch,
    capsys,
):
    settings = _settings(tmp_path)
    destination_calls = []
    session_calls = []
    prompt_calls = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: prompt_calls.append(("year", default)),
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: prompt_calls.append(("project",)),
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: prompt_calls.append(("day",)),
    )

    def destination(received_settings, **kwargs):
        destination_calls.append(
            (received_settings, kwargs)
        )
        return (
            tmp_path
            / "Photos_Master"
            / "2026"
            / "08"
            / "01_Ljubljana"
            / "Adriatic"
        )

    def run_session(received_settings, **kwargs):
        session_calls.append(
            (received_settings, kwargs)
        )
        return SimpleNamespace(
            batches_processed=2,
            copied=2,
            failed=0,
            completed=True,
            success=True,
        )

    monkeypatch.setattr(
        "mps.main.media_import_destination",
        destination,
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        run_session,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    exit_code = main(
        [
            "import",
            "--destination-year",
            "2026",
            "--destination-month-day",
            "08-01",
            "--destination-project",
            "Adriatic",
            "--destination-description",
            "Ljubljana",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert prompt_calls == []
    assert "Year        : 2026" in output
    assert "Date        : 08-01" in output
    assert "Project     : Adriatic" in output
    assert "Description : Ljubljana" in output
    assert "Day/session" not in output
    assert len(destination_calls) == 1
    assert len(session_calls) == 1

    destination_selection = destination_calls[0][1][
        "destination_selection"
    ]
    forwarded_selection = session_calls[0][1][
        "destination_selection"
    ]

    assert forwarded_selection is destination_selection
    assert destination_selection.year == 2026
    assert destination_selection.month_day == "08-01"
    assert destination_selection.project == "Adriatic"
    assert destination_selection.description == "Ljubljana"
    assert destination_calls[0] == (
        settings,
        {
            "year": 2026,
            "project": "Adriatic",
            "day": "08-01_Ljubljana",
            "destination_selection": destination_selection,
        },
    )
    assert session_calls[0][0] is settings
    assert session_calls[0][1]["year"] == 2026
    assert session_calls[0][1]["project"] == "Adriatic"
    assert session_calls[0][1]["day"] == "08-01_Ljubljana"


@pytest.mark.parametrize(
    "destination_arguments",
    [
        [
            "--destination-year",
            "2026",
            "--destination-month-day",
            "02-30",
            "--destination-project",
            "Adriatic",
            "--destination-description",
            "",
        ],
        [
            "--destination-year",
            "2026",
            "--destination-month-day",
            "08-01",
            "--destination-project",
            "Unsafe/Project",
            "--destination-description",
            "",
        ],
    ],
)
def test_cli_invalid_structured_destination_stops_before_import_work(
    destination_arguments,
    monkeypatch,
):
    work = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: work.append("settings"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: work.append("year"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: work.append("project"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: work.append("day"),
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: work.append("import"),
    )

    with pytest.raises(SystemExit):
        main(["import", *destination_arguments])

    assert work == []


@pytest.mark.parametrize("argument_mask", range(1, 15))
def test_cli_rejects_every_incomplete_destination_combination(
    argument_mask,
    monkeypatch,
):
    options = [
        ("--destination-year", "2026"),
        ("--destination-month-day", "08-01"),
        ("--destination-project", "Adriatic"),
        ("--destination-description", ""),
    ]
    arguments = ["import"]

    for index, option in enumerate(options):
        if argument_mask & (1 << index):
            arguments.extend(option)

    work = []
    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: work.append("settings"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: work.append("year"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: work.append("project"),
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: work.append("day"),
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: work.append("import"),
    )

    with pytest.raises(SystemExit):
        main(arguments)

    assert work == []


def test_cli_structured_destination_without_description_shows_dash(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.media_import_destination",
        lambda settings, **kwargs: tmp_path / "destination",
    )
    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        lambda *args, **kwargs: pytest.fail(
            "Import runner must not start after cancellation"
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n",
    )

    exit_code = main(
        [
            "import",
            "--destination-year",
            "2026",
            "--destination-month-day",
            "08-02",
            "--destination-project",
            "MPS GUI Test",
            "--destination-description",
            "",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Year        : 2026" in output
    assert "Date        : 08-02" in output
    assert "Project     : MPS GUI Test" in output
    assert "Description : —" in output
    assert "Day/session" not in output
