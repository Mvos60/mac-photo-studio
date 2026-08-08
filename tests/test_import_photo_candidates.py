from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.import_photo_candidates import build_import_photo_candidates


def _settings(tmp_path: Path) -> Settings:
    return Settings({
        "paths": {"photos_root": str(tmp_path / "Photos")},
        "media": {"raw_extensions": ["ARW"], "jpeg_extensions": ["JPG", "JPEG"]},
    })


def _card(root: Path, *, raw: int = 0, jpeg: int = 0) -> CardScanResult:
    return CardScanResult(
        root=root, dcim_path=root / "DCIM", raw_count=raw, jpeg_count=jpeg,
        heif_count=0, video_count=0, pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0), other_count=0,
        total_size_bytes=0,
    )


def _photo(root: Path, name: str, content: bytes = b"photo") -> Path:
    path = root / "DCIM" / "100MSDCF" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_candidates_group_pairs_and_keep_orphans_across_cards(tmp_path: Path):
    raw_card = tmp_path / "raw-card"
    jpg_card = tmp_path / "jpg-card"
    raw = _photo(raw_card, "DSC0001.arw", b"raw")
    jpg = _photo(jpg_card, "dsc0001.JPG", b"jpg")
    raw_only = _photo(raw_card, "DSC0002.ARW", b"raw-only")
    jpg_only = _photo(jpg_card, "DSC0003.jpeg", b"jpg-only")
    selection = ImportMediaSelection(sources=[
        _card(raw_card, raw=2), _card(jpg_card, jpeg=2),
    ])

    candidates = build_import_photo_candidates(selection, _settings(tmp_path))

    assert [candidate.key for candidate in candidates] == [
        "dsc0001", "dsc0002", "dsc0003",
    ]
    assert candidates[0].stem == "DSC0001"
    assert candidates[0].media_type == "RAW+JPG"
    assert set(candidates[0].source_paths) == {raw, jpg}
    assert candidates[1].source_paths == (raw_only,)
    assert candidates[1].media_type == "RAW"
    assert candidates[2].source_paths == (jpg_only,)
    assert candidates[2].media_type == "JPG"


def test_candidates_ignore_trash_and_processed_paths(tmp_path: Path):
    card = tmp_path / "card"
    processed = _photo(card, "DSC0001.ARW", b"one")
    trash = card / "DCIM" / ".Trash-1000" / "DSC0002.ARW"
    trash.parent.mkdir(parents=True)
    trash.write_bytes(b"trash")
    selection = ImportMediaSelection(sources=[_card(card, raw=1)])

    candidates = build_import_photo_candidates(
        selection, _settings(tmp_path), processed_source_files=[processed],
    )

    assert candidates == ()


def test_duplicate_raw_stem_is_retained_as_ambiguous(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_path = _photo(first, "DSC0001.ARW", b"first")
    second_path = _photo(second, "dsc0001.arw", b"second")
    selection = ImportMediaSelection(sources=[
        _card(first, raw=1), _card(second, raw=1),
    ])

    candidates = build_import_photo_candidates(selection, _settings(tmp_path))

    assert len(candidates) == 1
    assert candidates[0].ambiguous
    assert set(candidates[0].raw_paths) == {first_path, second_path}


def test_duplicate_jpeg_stem_is_retained_as_ambiguous(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_path = _photo(first, "DSC0001.JPG", b"first")
    second_path = _photo(second, "dsc0001.jpeg", b"second")
    selection = ImportMediaSelection(sources=[
        _card(first, jpeg=1), _card(second, jpeg=1),
    ])

    candidates = build_import_photo_candidates(selection, _settings(tmp_path))

    assert len(candidates) == 1
    assert candidates[0].ambiguous
    assert set(candidates[0].jpeg_paths) == {first_path, second_path}
