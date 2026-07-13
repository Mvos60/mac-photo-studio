from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

from mps.config import Settings
from mps.services.app_resolver import (
    ApplicationResolution,
)
from mps.services.workflow_application_context import (
    resolve_darktable_context,
    resolve_digikam_context,
    resolve_workflow_application_context,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(tmp_path),
            },
        }
    )


def test_resolves_available_application_version(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_application",
        lambda settings, key, command_name: (
            ApplicationResolution(
                name=key,
                found=True,
                method="PATH",
                command="/usr/bin/example",
                message="/usr/bin/example",
            )
        ),
    )

    called = []

    def run(command, **kwargs):
        called.append((command, kwargs))

        return CompletedProcess(
            command,
            0,
            stdout="example 5.6.0\n",
            stderr="",
        )

    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "subprocess.run",
        run,
    )

    result = resolve_workflow_application_context(
        settings=_settings(tmp_path),
        key="example",
        command_name="example",
        application="Example",
    )

    assert result.available is True
    assert result.application == "Example"
    assert result.version == "example 5.6.0"
    assert result.errors == ()
    assert called[0][0] == [
        "/usr/bin/example",
        "--version",
    ]


def test_preserves_flatpak_command(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_application",
        lambda settings, key, command_name: (
            ApplicationResolution(
                name=key,
                found=True,
                method="flatpak",
                command=(
                    "flatpak run org.example.Application"
                ),
                message="org.example.Application",
            )
        ),
    )

    called = []

    def run(command, **kwargs):
        called.append(command)

        return CompletedProcess(
            command,
            0,
            stdout="Example 1.2.3\n",
            stderr="",
        )

    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "subprocess.run",
        run,
    )

    result = resolve_workflow_application_context(
        settings=_settings(tmp_path),
        key="example",
        command_name="example",
        application="Example",
    )

    assert result.available is True
    assert result.version == "Example 1.2.3"
    assert called == [
        [
            "flatpak",
            "run",
            "org.example.Application",
            "--version",
        ]
    ]


def test_missing_application_is_reported(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_application",
        lambda settings, key, command_name: (
            ApplicationResolution(
                name=key,
                found=False,
                method="not found",
                command=None,
                message="not found",
            )
        ),
    )

    result = resolve_workflow_application_context(
        settings=_settings(tmp_path),
        key="example",
        command_name="example",
        application="Example",
    )

    assert result.available is False
    assert result.version is None
    assert result.errors == (
        "Example application was not found",
    )


def test_version_failure_does_not_hide_application(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_application",
        lambda settings, key, command_name: (
            ApplicationResolution(
                name=key,
                found=True,
                method="PATH",
                command="/usr/bin/example",
                message="/usr/bin/example",
            )
        ),
    )
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "subprocess.run",
        lambda *args, **kwargs: CompletedProcess(
            args[0],
            1,
            stdout="",
            stderr="version unavailable",
        ),
    )

    result = resolve_workflow_application_context(
        settings=_settings(tmp_path),
        key="example",
        command_name="example",
        application="Example",
    )

    assert result.available is True
    assert result.version is None
    assert result.errors == ()


def test_version_timeout_does_not_hide_application(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_application",
        lambda settings, key, command_name: (
            ApplicationResolution(
                name=key,
                found=True,
                method="PATH",
                command="/usr/bin/example",
                message="/usr/bin/example",
            )
        ),
    )
    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "subprocess.run",
        lambda *args, **kwargs: (
            _raise_timeout(args[0])
        ),
    )

    result = resolve_workflow_application_context(
        settings=_settings(tmp_path),
        key="example",
        command_name="example",
        application="Example",
    )

    assert result.available is True
    assert result.version is None


def _raise_timeout(command):
    raise TimeoutExpired(command, 10)


def test_digikam_context_uses_digikam_identity(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)
    called = []

    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_workflow_application_context",
        lambda **kwargs: called.append(kwargs)
        or "digikam-context",
    )

    result = resolve_digikam_context(
        settings
    )

    assert result == "digikam-context"
    assert called == [
        {
            "settings": settings,
            "key": "digikam",
            "command_name": "digikam",
            "application": "digiKam",
        }
    ]


def test_darktable_context_uses_darktable_identity(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)
    called = []

    monkeypatch.setattr(
        "mps.services.workflow_application_context."
        "resolve_workflow_application_context",
        lambda **kwargs: called.append(kwargs)
        or "darktable-context",
    )

    result = resolve_darktable_context(
        settings
    )

    assert result == "darktable-context"
    assert called == [
        {
            "settings": settings,
            "key": "darktable",
            "command_name": "darktable",
            "application": "darktable",
        }
    ]
