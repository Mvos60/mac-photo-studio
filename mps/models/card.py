from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CardScanResult:
    root: Path
    dcim_path: Path | None
    raw_count: int
    jpeg_count: int
    heif_count: int
    video_count: int
    pair_count: int
    orphan_raw_count: int
    orphan_jpeg_count: int
    other_count: int
    total_size_bytes: int

    @property
    def has_photos(self) -> bool:
        return self.raw_count > 0 or self.jpeg_count > 0 or self.heif_count > 0

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        data = asdict(self)
        data["root"] = str(self.root)
        data["dcim_path"] = str(self.dcim_path) if self.dcim_path is not None else None
        return data
