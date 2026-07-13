from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

from mps.config import Settings
from mps.services.app_resolver import (
    ApplicationResolution,
    resolve_application,
)


@dataclass(slots=True, frozen=True)
class WorkflowApplicationContext:
    key: str
    application: str
    available: bool
    version: str | None = None
    resolution: ApplicationResolution | None = None
    errors: tuple[str, ...] = ()


def _read_application_version(
    resolution: ApplicationResolution,
) -> str | None:
    if not resolution.found or not resolution.command:
        return None

    try:
        result = subprocess.run(
            [
                *shlex.split(resolution.command),
                "--version",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    output = (
        result.stdout.strip()
        or result.stderr.strip()
    )

    if result.returncode != 0 or not output:
        return None

    return output.splitlines()[0].strip()


def resolve_workflow_application_context(
    *,
    settings: Settings,
    key: str,
    command_name: str,
    application: str,
) -> WorkflowApplicationContext:
    resolution = resolve_application(
        settings,
        key,
        command_name,
    )

    if not resolution.found:
        return WorkflowApplicationContext(
            key=key,
            application=application,
            available=False,
            resolution=resolution,
            errors=(
                f"{application} application was not found",
            ),
        )

    return WorkflowApplicationContext(
        key=key,
        application=application,
        available=True,
        version=_read_application_version(
            resolution
        ),
        resolution=resolution,
    )


def resolve_digikam_context(
    settings: Settings,
) -> WorkflowApplicationContext:
    return resolve_workflow_application_context(
        settings=settings,
        key="digikam",
        command_name="digikam",
        application="digiKam",
    )


def resolve_darktable_context(
    settings: Settings,
) -> WorkflowApplicationContext:
    return resolve_workflow_application_context(
        settings=settings,
        key="darktable",
        command_name="darktable",
        application="darktable",
    )
