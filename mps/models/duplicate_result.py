from dataclasses import dataclass


@dataclass(slots=True)
class DuplicateResult:
    exists: bool
    identical: bool
    conflict: bool
