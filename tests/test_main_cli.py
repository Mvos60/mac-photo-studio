import json
from pathlib import Path

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
        }
    ]
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
