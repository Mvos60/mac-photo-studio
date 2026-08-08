from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


UNKNOWN_PHOTO_METADATA = "—"


@dataclass(frozen=True, slots=True)
class ImportPhotoCandidate:
    """One photographic capture offered by the native import selector."""

    key: str
    stem: str
    raw_paths: tuple[Path, ...] = ()
    jpeg_paths: tuple[Path, ...] = ()
    captured_at: str | None = None
    camera_model: str | None = None

    def __post_init__(self) -> None:
        if not self.raw_paths and not self.jpeg_paths:
            raise ValueError("A photo candidate requires at least one source path")

    @property
    def ambiguous(self) -> bool:
        return len(self.raw_paths) > 1 or len(self.jpeg_paths) > 1

    @property
    def media_type(self) -> str:
        if self.raw_paths and self.jpeg_paths:
            return "RAW+JPG"
        if self.raw_paths:
            return "RAW"
        return "JPG"

    @property
    def source_paths(self) -> tuple[Path, ...]:
        return self.raw_paths + self.jpeg_paths

    @property
    def display_captured_at(self) -> str:
        return self.captured_at or UNKNOWN_PHOTO_METADATA

    @property
    def display_camera_model(self) -> str:
        return self.camera_model or UNKNOWN_PHOTO_METADATA


@dataclass(frozen=True, slots=True)
class ImportPhotoSelectionResponse:
    selected_keys: frozenset[str]

    def selected_paths(
        self,
        candidates: tuple[ImportPhotoCandidate, ...],
    ) -> tuple[Path, ...]:
        paths: list[Path] = []
        for candidate in candidates:
            if candidate.key not in self.selected_keys:
                continue
            if candidate.ambiguous:
                raise ValueError("Ambiguous photo candidates cannot be selected")
            paths.extend(candidate.source_paths)
        return tuple(paths)
