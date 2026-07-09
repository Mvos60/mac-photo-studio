from pathlib import Path

from mps.config import Settings
from mps.main import main


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


def test_cli_plan_import_uses_year_first_layout(tmp_path, monkeypatch, capsys):
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
    assert str(tmp_path / "Photos_Master" / "2026" / "Adriatic" / "03_Slovenia") in output


def test_cli_real_import_copies_files_and_writes_provenance(tmp_path, monkeypatch, capsys):
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

    destination = tmp_path / "Photos_Master" / "2026" / "Adriatic" / "03_Slovenia"
    provenance_dir = destination / "provenance"
    index_file = provenance_dir / "certificate_index.json"

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mac Photo Studio Import" in output
    assert "Success:      True" in output

    assert (destination / "DSC0001.ARW").read_bytes() == b"raw-data"
    assert (destination / "DSC0001.JPG").read_bytes() == b"jpg-data"
    assert (destination / "mps_import.log").exists()

    assert provenance_dir.exists()
    assert index_file.exists()
    assert len(list(provenance_dir.glob("MPS-CERT-*.json"))) == 2

    index_text = index_file.read_text(encoding="utf-8")
    assert "DSC0001.ARW" in index_text
    assert "DSC0001.JPG" in index_text
