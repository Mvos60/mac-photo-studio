from dataclasses import dataclass, field


@dataclass(slots=True)
class ResumePlan:
    session_id: str
    resumable: bool
    verified_destinations: list[str] = field(default_factory=list)
    missing_destinations: list[str] = field(default_factory=list)
    conflict_destinations: list[str] = field(default_factory=list)

    @property
    def verified_count(self) -> int:
        return len(self.verified_destinations)

    @property
    def remaining_count(self) -> int:
        return len(self.missing_destinations)

    @property
    def conflict_count(self) -> int:
        return len(self.conflict_destinations)
