from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mps.config import Settings


@dataclass(frozen=True)
class PhotoPair:
    """A RAW/JPEG pair matched by original camera filename stem."""

    stem: str
    raw_path: Path
    jpeg_path: Path


@dataclass(frozen=True)
class PairingResult:
    """Result of a read-only RAW/JPEG pairing pass."""

    pairs: list[PhotoPair]
    raw_only: list[Path]
    jpeg_only: list[Path]

    @property
    def pair_count(self) -> int:
        return len(self.pairs)


def _extension_set(settings: Settings, key: str) -> set[str]:
    return {str(ext).lower().lstrip(".") for ext in settings.get(key, [])}


def _collect_files(folder: Path, extensions: set[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}

    if not folder.exists():
        return result

    for file in folder.rglob("*"):
        if not file.is_file():
            continue

        ext = file.suffix.lower().lstrip(".")
        if ext not in extensions:
            continue

        result[file.stem] = file

    return result


def pair_paths(raw_folder: Path, jpeg_folder: Path, settings: Settings) -> PairingResult:
    """Pair RAW and JPEG files by filename stem.

    This operation is strictly read-only.
    """

    raw_extensions = _extension_set(settings, "media.raw_extensions")
    jpeg_extensions = _extension_set(settings, "media.jpeg_extensions")

    raw_files = _collect_files(raw_folder.expanduser(), raw_extensions)
    jpeg_files = _collect_files(jpeg_folder.expanduser(), jpeg_extensions)

    paired_stems = sorted(set(raw_files) & set(jpeg_files))
    raw_only_stems = sorted(set(raw_files) - set(jpeg_files))
    jpeg_only_stems = sorted(set(jpeg_files) - set(raw_files))

    pairs = [
        PhotoPair(stem=stem, raw_path=raw_files[stem], jpeg_path=jpeg_files[stem])
        for stem in paired_stems
    ]

    return PairingResult(
        pairs=pairs,
        raw_only=[raw_files[stem] for stem in raw_only_stems],
        jpeg_only=[jpeg_files[stem] for stem in jpeg_only_stems],
    )
