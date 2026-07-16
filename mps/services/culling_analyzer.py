from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndexEntry,
)
from mps.services.imported_photo_registry import file_sha256
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import load_index


class CullingCandidateStatus(str, Enum):
    CULL_CANDIDATE = "cull_candidate"
    PROVENANCE_CLEANUP_CANDIDATE = (
        "provenance_cleanup_candidate"
    )
    RAW_HASH_MISMATCH = "raw_hash_mismatch"
    NO_ACTION = "no_action"


@dataclass(frozen=True, slots=True)
class MissingImportedJpeg:
    stem: str
    jpeg_path: Path
    jpeg_provenance_id: str
    jpeg_sha256: str
    raw_path: Path | None
    raw_provenance_id: str | None
    raw_sha256: str | None
    raw_hash_matches: bool

    @property
    def has_imported_raw(self) -> bool:
        return self.raw_path is not None

    @property
    def has_surviving_raw(self) -> bool:
        return (
            self.raw_path is not None
            and self.raw_path.exists()
        )

    @property
    def status(self) -> CullingCandidateStatus:
        if not self.has_imported_raw:
            return (
                CullingCandidateStatus
                .PROVENANCE_CLEANUP_CANDIDATE
            )

        if (
            self.has_surviving_raw
            and self.raw_hash_matches
        ):
            return (
                CullingCandidateStatus
                .CULL_CANDIDATE
            )

        if self.has_surviving_raw:
            return (
                CullingCandidateStatus
                .RAW_HASH_MISMATCH
            )

        return CullingCandidateStatus.NO_ACTION

    @property
    def is_orphan_raw_candidate(self) -> bool:
        return (
            self.status
            == CullingCandidateStatus.CULL_CANDIDATE
        )

    @property
    def is_provenance_cleanup_candidate(
        self,
    ) -> bool:
        return (
            self.status
            == (
                CullingCandidateStatus
                .PROVENANCE_CLEANUP_CANDIDATE
            )
        )

    @property
    def is_actionable(self) -> bool:
        return self.status in {
            CullingCandidateStatus.CULL_CANDIDATE,
            (
                CullingCandidateStatus
                .PROVENANCE_CLEANUP_CANDIDATE
            ),
        }


@dataclass(frozen=True, slots=True)
class CullingAnalysis:
    import_root: Path
    missing_jpegs: list[MissingImportedJpeg]

    @property
    def missing_jpeg_count(self) -> int:
        return len(self.missing_jpegs)

    @property
    def orphan_raw_candidate_count(self) -> int:
        return sum(
            item.is_orphan_raw_candidate
            for item in self.missing_jpegs
        )

    @property
    def provenance_cleanup_candidate_count(
        self,
    ) -> int:
        return sum(
            item.is_provenance_cleanup_candidate
            for item in self.missing_jpegs
        )

    @property
    def actionable_candidate_count(self) -> int:
        return sum(
            item.is_actionable
            for item in self.missing_jpegs
        )

    @property
    def orphan_raw_candidates(
        self,
    ) -> list[MissingImportedJpeg]:
        return [
            item
            for item in self.missing_jpegs
            if item.is_orphan_raw_candidate
        ]

    @property
    def provenance_cleanup_candidates(
        self,
    ) -> list[MissingImportedJpeg]:
        return [
            item
            for item in self.missing_jpegs
            if item.is_provenance_cleanup_candidate
        ]

    @property
    def actionable_candidates(
        self,
    ) -> list[MissingImportedJpeg]:
        return [
            item
            for item in self.missing_jpegs
            if item.is_actionable
        ]


def _extension_set(
    settings: Settings,
    key: str,
) -> set[str]:
    return {
        str(extension).lower().lstrip(".")
        for extension in settings.get(key, [])
    }


def _entry_path(
    entry: ProvenanceCertificateIndexEntry,
) -> Path:
    return Path(entry.destination_path).expanduser()


def _entries_by_stem(
    entries: list[ProvenanceCertificateIndexEntry],
    extensions: set[str],
) -> dict[str, ProvenanceCertificateIndexEntry]:
    result: dict[
        str,
        ProvenanceCertificateIndexEntry,
    ] = {}

    for entry in entries:
        path = _entry_path(entry)
        extension = (
            path.suffix.lower().lstrip(".")
        )

        if extension not in extensions:
            continue

        result[path.stem] = entry

    return result


def _raw_hash_matches(
    raw_path: Path | None,
    expected_sha256: str | None,
) -> bool:
    if (
        raw_path is None
        or expected_sha256 is None
        or not raw_path.exists()
        or not raw_path.is_file()
    ):
        return False

    try:
        return (
            file_sha256(raw_path)
            == expected_sha256
        )
    except OSError:
        return False


def analyze_culling(
    import_root: str | Path,
    settings: Settings,
) -> CullingAnalysis:
    root = Path(import_root).expanduser()
    certificate_index_path = index_path(root)

    if not certificate_index_path.exists():
        return CullingAnalysis(
            import_root=root,
            missing_jpegs=[],
        )

    try:
        certificate_index = load_index(
            certificate_index_path
        )
    except (
        OSError,
        ValueError,
        KeyError,
    ):
        return CullingAnalysis(
            import_root=root,
            missing_jpegs=[],
        )

    raw_extensions = _extension_set(
        settings,
        "media.raw_extensions",
    )
    jpeg_extensions = _extension_set(
        settings,
        "media.jpeg_extensions",
    )

    raw_entries = _entries_by_stem(
        certificate_index.entries,
        raw_extensions,
    )
    jpeg_entries = _entries_by_stem(
        certificate_index.entries,
        jpeg_extensions,
    )

    missing_jpegs: list[
        MissingImportedJpeg
    ] = []

    for stem in sorted(jpeg_entries):
        jpeg_entry = jpeg_entries[stem]
        jpeg_path = _entry_path(jpeg_entry)

        if jpeg_path.exists():
            continue

        raw_entry = raw_entries.get(stem)

        if raw_entry is None:
            raw_path = None
            raw_provenance_id = None
            raw_sha256 = None
        else:
            raw_path = _entry_path(raw_entry)
            raw_provenance_id = (
                raw_entry.provenance_id
            )
            raw_sha256 = raw_entry.sha256

        missing_jpegs.append(
            MissingImportedJpeg(
                stem=stem,
                jpeg_path=jpeg_path,
                jpeg_provenance_id=(
                    jpeg_entry.provenance_id
                ),
                jpeg_sha256=jpeg_entry.sha256,
                raw_path=raw_path,
                raw_provenance_id=(
                    raw_provenance_id
                ),
                raw_sha256=raw_sha256,
                raw_hash_matches=(
                    _raw_hash_matches(
                        raw_path,
                        raw_sha256,
                    )
                ),
            )
        )

    return CullingAnalysis(
        import_root=root,
        missing_jpegs=missing_jpegs,
    )
