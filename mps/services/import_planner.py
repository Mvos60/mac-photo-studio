from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mps.config import Settings
from mps.services.pairing import PairingResult, pair_paths


@dataclass(frozen=True)
class ImportPlan:
    """A read-only plan describing a future import."""

    project: str
    day: str
    raw_folder: Path
    jpeg_folder: Path
    destination: Path
    pairing: PairingResult
    estimated_size_bytes: int
    warnings: list[str]

    @property
    def total_source_files(self) -> int:
        return self.pairing.pair_count * 2 + len(self.pairing.raw_only) + len(self.pairing.jpeg_only)


def _file_list_size(files: list[Path]) -> int:
    total = 0
    for file in files:
        try:
            total += file.stat().st_size
        except OSError:
            pass
    return total


def create_import_plan(
    project: str,
    day: str,
    raw_folder: Path,
    jpeg_folder: Path,
    settings: Settings,
) -> ImportPlan:
    """Create a read-only import plan.

    The planner does not create folders, copy files, rename files, or modify sources.
    """

    photos_root = Path(settings.get("paths.photos_root", "~/Photos_Master")).expanduser()
    destination = photos_root / project / day

    pairing = pair_paths(raw_folder, jpeg_folder, settings)
    warnings: list[str] = []

    if pairing.raw_only:
        warnings.append(f"{len(pairing.raw_only)} RAW file(s) have no matching JPEG")

    if pairing.jpeg_only:
        warnings.append(f"{len(pairing.jpeg_only)} JPEG file(s) have no matching RAW")

    files: list[Path] = []
    for pair in pairing.pairs:
        files.append(pair.raw_path)
        files.append(pair.jpeg_path)
    files.extend(pairing.raw_only)
    files.extend(pairing.jpeg_only)

    return ImportPlan(
        project=project,
        day=day,
        raw_folder=raw_folder.expanduser(),
        jpeg_folder=jpeg_folder.expanduser(),
        destination=destination,
        pairing=pairing,
        estimated_size_bytes=_file_list_size(files),
         warnings=warnings,
    )
