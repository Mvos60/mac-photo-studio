from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from mps.config import Settings
from mps.services.app_resolver import resolve_application


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    ok: bool
    message: str


def run_health_checks(settings: Settings) -> list[HealthCheckResult]:
    photos_root = Path(settings.get("paths.photos_root", "~/Photos_Master")).expanduser()
    digikam = resolve_application(settings, "digikam", "digikam")
    darktable = resolve_application(settings, "darktable", "darktable")

    return [
        HealthCheckResult("Photos root", photos_root.exists(), str(photos_root)),
        HealthCheckResult("Python", shutil.which("python3") is not None, shutil.which("python3") or "not found"),
        HealthCheckResult("digiKam", digikam.found, f"{digikam.method}: {digikam.message}"),
        HealthCheckResult("darktable", darktable.found, f"{darktable.method}: {darktable.message}"),
        HealthCheckResult("rsync", shutil.which("rsync") is not None, shutil.which("rsync") or "not found"),
        HealthCheckResult("exiftool", shutil.which("exiftool") is not None, shutil.which("exiftool") or "not found"),
    ]
