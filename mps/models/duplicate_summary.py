from dataclasses import dataclass


@dataclass(slots=True)
class DuplicateSummary:
    checked: int
    missing: int
    identical: int
    conflicts: int

    @property
    def safe_to_continue(self) -> bool:
        return self.conflicts == 0
