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


def test_cli_import_command_cancel_does_not_run_real_import(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.run_interactive_import",
        lambda settings: None,
    )
    monkeypatch.setattr(
        "mps.main.run_real_import",
        lambda *args: called.append(args),
    )

    exit_code = main(["import"])

    assert exit_code == 0
    assert called == []


def test_cli_import_command_hands_wizard_session_to_real_import(
    tmp_path,
    monkeypatch,
):
    session = ImportSessionRequest(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=Path("/media/raw"),
        jpeg_folder=Path("/media/jpg"),
    )

    called = []

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: _settings(tmp_path),
    )
    monkeypatch.setattr(
        "mps.main.run_interactive_import",
        lambda settings: session,
    )
    monkeypatch.setattr(
        "mps.main.run_real_import",
        lambda *args: called.append(args) or 0,
    )

    exit_code = main(["import"])

    assert exit_code == 0
    assert called == [
        (
            2026,
            "Adriatic",
            "03_Slovenia",
            "/media/raw",
            "/media/jpg",
        )
    ]
