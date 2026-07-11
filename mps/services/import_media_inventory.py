from __future__ import annotations

from mps.models.import_media_inventory import (
    ImportMediaInventory,
    ImportMediaKind,
)
from mps.models.import_media_selection import ImportMediaSelection


def classify_import_media(
    selection: ImportMediaSelection,
) -> ImportMediaInventory:
    if selection.empty:
        kind = ImportMediaKind.EMPTY
    elif selection.has_raw and selection.has_jpeg:
        kind = ImportMediaKind.RAW_AND_JPEG
    elif selection.has_raw:
        kind = ImportMediaKind.RAW_ONLY
    else:
        kind = ImportMediaKind.JPEG_ONLY

    return ImportMediaInventory(
        selection=selection,
        kind=kind,
    )
