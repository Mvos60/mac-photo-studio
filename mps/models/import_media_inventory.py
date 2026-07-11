from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mps.models.import_media_selection import ImportMediaSelection


class ImportMediaKind(str, Enum):
    EMPTY = "EMPTY"
    RAW_ONLY = "RAW_ONLY"
    JPEG_ONLY = "JPEG_ONLY"
    RAW_AND_JPEG = "RAW_AND_JPEG"


@dataclass(slots=True, frozen=True)
class ImportMediaInventory:
    selection: ImportMediaSelection
    kind: ImportMediaKind

    @property
    def complete_pair_inventory(self) -> bool:
        return (
            self.kind == ImportMediaKind.RAW_AND_JPEG
            and self.selection.total_raw_files
            == self.selection.total_jpeg_files
        )
