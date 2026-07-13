from __future__ import annotations

from enum import StrEnum


class ProvenanceEventType(StrEnum):
    INGEST = "ingest"
    EDIT = "edit"
    DERIVATIVE = "derivative"
    EXPORT = "export"
    VERIFY = "verify"
