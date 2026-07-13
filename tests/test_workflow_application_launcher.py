from pathlib import Path

from mps.config import Settings
from mps.services.app_resolver import ApplicationResolution
from mps.services.workflow_application_launcher import (
    launch_darktable,
    launch_digikam,
    launch_workflow_application,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
        }
    )


def test_launch_application_uses_resolved_command(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "resolve_application",
        lambda settings, key, command_name:
        ApplicationResolution(
            name=key,
            found=True,
            method="configured",
            command="/opt/photo app",
            message="found",
        ),
    )

    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "subprocess.Popen",
        lambda command, **kwargs: called.append(
            (command, kwargs)
        ),
    )

    target = tmp_path / "Photos_Master"

    result = launch_workflow_application(
        settings=_settings(tmp_path),
        key="photo",
        command_name="photo",
        application="Photo",
        target=target,
    )

    assert result.launched is True
    assert result.command == (
        "/opt/photo",
        "app",
        str(target),
    )
    assert called[0][0] == result.command
    assert called[0][1]["start_new_session"] is True


def test_launch_application_reports_missing_application(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "resolve_application",
        lambda settings, key, command_name:
        ApplicationResolution(
            name=key,
            found=False,
            method="not found",
            command=None,
            message="not found",
        ),
    )

    result = launch_workflow_application(
        settings=_settings(tmp_path),
        key="photo",
        command_name="photo",
        application="Photo",
        target=tmp_path,
    )

    assert result.launched is False
    assert result.errors == (
        "Photo application was not found",
    )


def test_launch_application_reports_os_error(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "resolve_application",
        lambda settings, key, command_name:
        ApplicationResolution(
            name=key,
            found=True,
            method="PATH",
            command="/usr/bin/photo",
            message="found",
        ),
    )

    def fail(*args, **kwargs):
        raise OSError("launch failed")

    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "subprocess.Popen",
        fail,
    )

    result = launch_workflow_application(
        settings=_settings(tmp_path),
        key="photo",
        command_name="photo",
        application="Photo",
        target=tmp_path,
    )

    assert result.launched is False
    assert result.errors == ("launch failed",)


def test_launch_digikam_targets_import_root(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)
    called = []

    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "launch_workflow_application",
        lambda **kwargs: called.append(kwargs)
        or "digikam-launch",
    )

    result = launch_digikam(
        settings=settings,
        import_root=tmp_path / "import",
    )

    assert result == "digikam-launch"
    assert called == [
        {
            "settings": settings,
            "key": "digikam",
            "command_name": "digikam",
            "application": "digiKam",
            "target": tmp_path / "import",
        }
    ]


def test_launch_darktable_targets_photo(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)
    called = []

    monkeypatch.setattr(
        "mps.services.workflow_application_launcher."
        "launch_workflow_application",
        lambda **kwargs: called.append(kwargs)
        or "darktable-launch",
    )

    result = launch_darktable(
        settings=settings,
        photo_path=tmp_path / "DSC0001.ARW",
    )

    assert result == "darktable-launch"
    assert called == [
        {
            "settings": settings,
            "key": "darktable",
            "command_name": "darktable",
            "application": "darktable",
            "target": tmp_path / "DSC0001.ARW",
        }
    ]
