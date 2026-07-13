from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from mps.config import Settings
from mps.services.app_resolver import resolve_application


@dataclass(slots=True, frozen=True)
class WorkflowApplicationLaunch:
    application: str
    launched: bool
    target: Path
    command: tuple[str, ...] = ()
    errors: tuple[str, ...] = field(default_factory=tuple)


def launch_workflow_application(
    *,
    settings: Settings,
    key: str,
    command_name: str,
    application: str,
    target: str | Path,
) -> WorkflowApplicationLaunch:
    path = Path(target).expanduser()

    resolution = resolve_application(
        settings,
        key,
        command_name,
    )

    if not resolution.found or not resolution.command:
        return WorkflowApplicationLaunch(
            application=application,
            launched=False,
            target=path,
            errors=(
                f"{application} application was not found",
            ),
        )

    command = (
        *shlex.split(resolution.command),
        str(path),
    )

    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return WorkflowApplicationLaunch(
            application=application,
            launched=False,
            target=path,
            command=tuple(command),
            errors=(str(exc),),
        )

    return WorkflowApplicationLaunch(
        application=application,
        launched=True,
        target=path,
        command=tuple(command),
    )


def launch_digikam(
    *,
    settings: Settings,
    import_root: str | Path,
) -> WorkflowApplicationLaunch:
    return launch_workflow_application(
        settings=settings,
        key="digikam",
        command_name="digikam",
        application="digiKam",
        target=import_root,
    )


def launch_darktable(
    *,
    settings: Settings,
    photo_path: str | Path,
) -> WorkflowApplicationLaunch:
    return launch_workflow_application(
        settings=settings,
        key="darktable",
        command_name="darktable",
        application="darktable",
        target=photo_path,
    )
