from pathlib import Path
from subprocess import CompletedProcess

from mps.services.camera_identifier import UNKNOWN_CAMERA, identify_camera_model


def test_identify_camera_model_returns_unknown_for_missing_file(tmp_path):
    missing = tmp_path / "missing.ARW"

    assert identify_camera_model(missing) == UNKNOWN_CAMERA


def test_identify_camera_model_returns_model_from_exiftool(tmp_path, monkeypatch):
    photo = tmp_path / "DSC0001.JPG"
    photo.write_bytes(b"jpeg-data")

    def fake_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="ILCE-7M3\n",
            stderr="",
        )

    monkeypatch.setattr(
        "mps.services.camera_identifier.subprocess.run",
        fake_run,
    )

    assert identify_camera_model(photo) == "ILCE-7M3"


def test_identify_camera_model_returns_unknown_when_exiftool_fails(tmp_path, monkeypatch):
    photo = tmp_path / "DSC0001.ARW"
    photo.write_bytes(b"raw-data")

    def fake_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="bad file",
        )

    monkeypatch.setattr(
        "mps.services.camera_identifier.subprocess.run",
        fake_run,
    )

    assert identify_camera_model(photo) == UNKNOWN_CAMERA


def test_identify_camera_model_returns_unknown_when_model_is_empty(tmp_path, monkeypatch):
    photo = tmp_path / "DSC0001.JPG"
    photo.write_bytes(b"jpeg-data")

    def fake_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="\n",
            stderr="",
        )

    monkeypatch.setattr(
        "mps.services.camera_identifier.subprocess.run",
        fake_run,
    )

    assert identify_camera_model(photo) == UNKNOWN_CAMERA
