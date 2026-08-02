from pathlib import Path
import json

import pytest

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)
from mps.services.import_media_wizard_runner import (
    run_import_media_session,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


def _write_photo(
    root: Path,
    name: str,
    content: bytes,
) -> None:
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True, exist_ok=True)
    (dcim / name).write_bytes(content)


def _card(
    root: Path,
    *,
    raw: int = 0,
    jpeg: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
        raw_count=raw,
        jpeg_count=jpeg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0),
        other_count=0,
        total_size_bytes=0,
    )


def test_single_raw_card_can_finish_session(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    selections = iter(
        [
            ImportMediaSelection(
                sources=[
                    _card(root, raw=1),
                ]
            ),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: next(selections),
    )

    prompts = []

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: prompts.append(prompt) or "no",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-TEST",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 1
    assert result.copied == 1
    assert len(result.session.sources) == 1
    assert "same photo session" in output
    assert "matching RAW or JPG card" in output
    assert "Press Enter to scan" in prompts[0]
    assert "type no only when all cards are imported" in prompts[0]


def test_raw_then_jpeg_same_reader_are_processed_sequentially(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    raw_selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    jpeg_selection = ImportMediaSelection(
        sources=[
            _card(root, jpeg=1),
        ]
    )

    discovery_count = 0

    def discover(settings):
        nonlocal discovery_count
        discovery_count += 1

        if discovery_count == 1:
            return raw_selection

        raw_file = (
            root
            / "DCIM"
            / "100MSDCF"
            / "DSC0001.ARW"
        )

        if raw_file.exists():
            raw_file.unlink()

        jpeg_file = (
            root
            / "DCIM"
            / "100MSDCF"
            / "DSC0001.JPG"
        )

        if not jpeg_file.exists():
            jpeg_file.write_bytes(b"jpeg-data")

        return jpeg_selection

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        discover,
    )

    answers = iter(["", "no"])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-SEQUENTIAL",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 2
    assert result.copied == 2
    assert len(result.session.sources) == 2

    assert {
        path.name
        for path in result.session.processed_source_files
    } == {
        "DSC0001.ARW",
        "DSC0001.JPG",
    }

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "DSC0001.JPG").exists()

    assert output.count("same photo session") == 2
    assert "Final Import Session Reconciliation" in output
    assert "FINAL STATUS       : IMPORT SESSION RECONCILED" in output


def test_two_simultaneous_cards_are_one_batch(
    monkeypatch,
    tmp_path: Path,
):
    raw_root = tmp_path / "raw"
    jpeg_root = tmp_path / "jpeg"

    _write_photo(raw_root, "DSC0001.ARW", b"raw-data")
    _write_photo(jpeg_root, "DSC0001.JPG", b"jpeg-data")

    selection = ImportMediaSelection(
        sources=[
            _card(raw_root, raw=1),
            _card(jpeg_root, jpeg=1),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: selection,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "no",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-TWO-READERS",
    )

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 1
    assert result.copied == 2
    assert len(result.session.sources) == 2


def test_no_media_does_not_complete_session(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: ImportMediaSelection(
            sources=[]
        ),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-EMPTY",
    )

    output = capsys.readouterr().out

    assert result.success is False
    assert result.completed is False
    assert result.batches_processed == 0
    assert "No new photo media available." in output




def test_same_card_rescan_defaults_to_retry(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    discovery_count = 0

    def discover(settings):
        nonlocal discovery_count
        discovery_count += 1

        if discovery_count < 3:
            return selection

        return ImportMediaSelection(sources=[])

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        discover,
    )

    answers = iter(["", "", "no"])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-RESCAN",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.batches_processed == 1
    assert result.copied == 1
    assert discovery_count == 3
    assert (
        "Mounted photo media has already been processed "
        "in this session."
    ) in output
    assert (
        "Eject or unmount the processed media and "
        "insert the next card from the same photo session."
    ) in output


def test_empty_reader_after_batch_retries_until_explicit_no(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    first_selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    empty_selection = ImportMediaSelection(sources=[])

    discoveries = iter(
        [
            first_selection,
            empty_selection,
            empty_selection,
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: next(discoveries),
    )

    answers = iter(["", "", "no"])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-EMPTY-READER",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.batches_processed == 1
    assert result.copied == 1
    assert "No new media is mounted." in output
    assert output.count("Searching for photo media...") == 3
    assert "FINAL STATUS       : IMPORT SESSION RECONCILED" in output


def test_successful_batch_saves_active_session_state(
    monkeypatch,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    state_path = tmp_path / "active_session.json"

    _write_photo(root, "DSC0001.ARW", b"raw-data")

    selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: selection,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "no",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-PERSIST",
        session_state_path=state_path,
    )

    assert result.success
    assert state_path.exists() is False


def test_interrupted_after_first_batch_leaves_session_state(
    monkeypatch,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    state_path = tmp_path / "active_session.json"

    _write_photo(root, "DSC0001.ARW", b"raw-data")

    selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: selection,
    )

    def interrupt(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "builtins.input",
        interrupt,
    )

    try:
        run_import_media_session(
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="03_Slovenia",
            session_id="MPS-SESSION-INTERRUPTED",
            session_state_path=state_path,
        )
    except KeyboardInterrupt:
        pass

    assert state_path.exists()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "destination" not in state

    from mps.services.import_media_session_store import (
        load_import_media_session,
    )

    restored = load_import_media_session(state_path)

    assert restored.session_id == "MPS-SESSION-INTERRUPTED"
    assert len(restored.source_fingerprints) == 1
    assert [
        path.name
        for path in restored.processed_source_files
    ] == [
        "DSC0001.ARW",
    ]


def test_loaded_session_continues_same_session_id(
    monkeypatch,
    tmp_path: Path,
):
    from mps.models.import_media_session import ImportMediaSession
    from mps.services.import_media_session_store import (
        load_import_media_session,
        save_import_media_session,
    )
    from mps.services.media_source_identity import (
        media_source_fingerprint,
    )

    reader = tmp_path / "reader"
    state_path = tmp_path / "active_session.json"
    settings = _settings(tmp_path)

    _write_photo(reader, "DSC0001.ARW", b"raw-data")

    raw_card = _card(reader, raw=1)

    first_session = ImportMediaSession(
        session_id="MPS-SESSION-RESUME",
        source_fingerprints={
            media_source_fingerprint(raw_card),
        },
        processed_source_files=[
            reader
            / "DCIM"
            / "100MSDCF"
            / "DSC0001.ARW"
        ],
    )

    save_import_media_session(
        first_session,
        state_path,
    )

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    from mps.services.import_media_batch_processor import (
        process_import_media_batch,
    )

    evidence_session = ImportMediaSession()

    first_result = process_import_media_batch(
        ImportMediaSelection(
            sources=[raw_card]
        ),
        evidence_session,
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-RESUME",
    )

    assert first_result.success

    raw_file = (
        reader
        / "DCIM"
        / "100MSDCF"
        / "DSC0001.ARW"
    )
    raw_file.unlink()

    _write_photo(reader, "DSC0001.JPG", b"jpeg-data")

    jpeg_selection = ImportMediaSelection(
        sources=[
            _card(reader, jpeg=1),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda current_settings: jpeg_selection,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "no",
    )

    restored = load_import_media_session(state_path)

    result = run_import_media_session(
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session=restored,
        session_state_path=state_path,
    )

    assert result.success
    assert result.session_id == "MPS-SESSION-RESUME"
    assert result.reconciliation is not None
    assert result.reconciliation.session_id_matches is True
    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "DSC0001.JPG").exists()
    assert state_path.exists() is False


def test_import_media_session_forwards_progress_callback(
    monkeypatch,
    tmp_path: Path,
):
    root = tmp_path / "progress-card"
    _write_photo(root, "DSC0099.ARW", b"raw-data")

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "no",
    )

    seen: list[
        tuple[str, int, int, int, str]
    ] = []

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Progress Test",
        day="01-08-2026",
        session_id="MPS-SESSION-PROGRESS",
        progress_callback=lambda progress: seen.append(
            (
                progress.phase,
                progress.current,
                progress.total,
                progress.percent,
                progress.source.name,
            )
        ),
    )

    assert result.success
    assert seen == [
        ("checking", 0, 1, 0, "DSC0099.ARW"),
        ("checking", 1, 1, 100, "DSC0099.ARW"),
        ("copying", 0, 1, 0, "DSC0099.ARW"),
        ("copying", 1, 1, 100, "DSC0099.ARW"),
        ("provenance", 0, 1, 0, "DSC0099.ARW"),
        ("provenance", 1, 1, 100, "DSC0099.ARW"),
        ("verifying", 0, 1, 0, "01-08-2026"),
        ("verifying", 1, 1, 100, "01-08-2026"),
    ]

def test_duplicate_only_media_finishes_cleanly(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    from mps.models.import_media_session import (
        ImportMediaSession,
    )
    from mps.services.import_media_batch_processor import (
        process_import_media_batch,
    )

    root = tmp_path / "reader"
    settings = _settings(tmp_path)
    selection = ImportMediaSelection(
        sources=[
            _card(root, jpeg=1),
        ]
    )

    _write_photo(
        root,
        "DSC0001.JPG",
        b"jpeg-photo",
    )

    first = process_import_media_batch(
        selection,
        ImportMediaSession(),
        settings,
        year=2026,
        project="First",
        day="Session",
        session_id="MPS-SESSION-FIRST",
    )

    assert first.success

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda current_settings: selection,
    )

    result = run_import_media_session(
        settings,
        year=2026,
        project="Second",
        day="Session",
        session_id="MPS-SESSION-NOOP",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.completed is True
    assert result.nothing_to_import is True
    assert result.batches_processed == 0
    assert result.copied == 0
    assert result.failed == 0
    assert "No new photo files found." in output
    assert (
        "All discovered photo files were already imported."
        in output
    )
    assert "Media batch processing failed." not in output

def test_sequential_batches_reuse_same_calendar_destination_selection(
    monkeypatch,
    tmp_path: Path,
):
    from mps.services.import_media_batch_processor import (
        process_import_media_batch as real_process_import_media_batch,
    )

    root = tmp_path / "reader"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    raw_selection = ImportMediaSelection(
        sources=[_card(root, raw=1)]
    )
    jpeg_selection = ImportMediaSelection(
        sources=[_card(root, jpeg=1)]
    )
    discovery_count = 0

    def discover(settings):
        nonlocal discovery_count
        discovery_count += 1

        if discovery_count == 1:
            return raw_selection

        raw_file = (
            root / "DCIM" / "100MSDCF" / "DSC0001.ARW"
        )
        raw_file.unlink(missing_ok=True)
        jpeg_file = (
            root / "DCIM" / "100MSDCF" / "DSC0001.JPG"
        )
        if not jpeg_file.exists():
            jpeg_file.write_bytes(b"jpeg-data")
        return jpeg_selection

    received_selections = []
    received_destinations = []
    saved_destinations = []

    def process(*args, **kwargs):
        received_selections.append(
            kwargs["destination_selection"]
        )
        result = real_process_import_media_batch(
            *args,
            **kwargs,
        )
        received_destinations.append(result.plan.destination)
        return result

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        discover,
    )
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "process_import_media_batch",
        process,
    )
    from mps.services.import_media_session_store import (
        save_import_media_session as real_save_import_media_session,
    )

    def save(session, path):
        saved_destinations.append(session.destination)
        return real_save_import_media_session(session, path)

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "save_import_media_session",
        save,
    )
    answers = iter(["", "no"])
    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
    )
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=1999,
        project="Legacy Project",
        day="Legacy Day",
        destination_selection=destination_selection,
        session_id="MPS-SESSION-CALENDAR-SEQUENTIAL",
        session_state_path=tmp_path / "active_session.json",
    )

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )

    assert result.success
    assert result.batches_processed == 2
    assert received_selections == [
        destination_selection,
        destination_selection,
    ]
    assert received_selections[0] is destination_selection
    assert received_selections[1] is destination_selection
    assert received_destinations == [
        destination,
        destination,
    ]
    assert len(saved_destinations) == 2
    assert saved_destinations[0] is saved_destinations[1]
    assert saved_destinations[0] is not None
    assert saved_destinations[0].selection is destination_selection
    assert saved_destinations[0].import_root == destination
    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "DSC0001.JPG").exists()


def test_first_verified_structured_batch_saves_destination(
    monkeypatch,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    state_path = tmp_path / "active_session.json"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner.discover_import_media",
        lambda settings: ImportMediaSelection(sources=[_card(root, raw=1)]),
    )

    def interrupt(_):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )

    with pytest.raises(KeyboardInterrupt):
        run_import_media_session(
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="08-01_Ljubljana",
            destination_selection=destination_selection,
            session_id="MPS-SESSION-STRUCTURED",
            session_state_path=state_path,
        )

    from mps.services.import_media_session_store import (
        load_import_media_session,
    )

    restored = load_import_media_session(state_path)
    assert restored.destination is not None
    assert restored.destination.selection == destination_selection
    assert restored.destination.import_root == (
        tmp_path / "Photos_Master" / "2026" / "08"
        / "01_Ljubljana" / "Adriatic"
    )


@pytest.mark.parametrize("conflict", ["selection", "import_root"])
def test_conflicting_structured_destination_is_not_overwritten(
    monkeypatch,
    tmp_path: Path,
    conflict: str,
):
    root = tmp_path / "reader"
    state_path = tmp_path / "active_session.json"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    incoming = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )
    existing_selection = (
        ImportDestinationSelection(
            year=2026,
            month_day="08-02",
            project="Adriatic",
            description="Ljubljana",
        )
        if conflict == "selection"
        else incoming
    )
    existing_root = (
        tmp_path / "conflicting-root"
        if conflict == "import_root"
        else incoming.destination_path(tmp_path / "Photos_Master")
    )
    existing = ImportMediaSessionDestination(
        selection=existing_selection,
        import_root=existing_root,
    )
    session = ImportMediaSession(destination=existing)
    processor_calls = []

    def process(*args, **kwargs):
        processor_calls.append((args, kwargs))
        raise AssertionError("processor must not be called")

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "process_import_media_batch",
        process,
    )
    original_state = b"unchanged active state"
    state_path.write_bytes(original_state)
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner.discover_import_media",
        lambda settings: ImportMediaSelection(sources=[_card(root, raw=1)]),
    )

    with pytest.raises(ValueError, match="conflicts"):
        run_import_media_session(
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="08-01_Ljubljana",
            destination_selection=incoming,
            session=session,
            session_state_path=state_path,
        )

    assert session.destination is existing
    assert processor_calls == []
    assert state_path.read_bytes() == original_state
    assert not incoming.destination_path(
        tmp_path / "Photos_Master"
    ).exists()


def test_stored_structured_destination_requires_selection(
    monkeypatch,
    tmp_path: Path,
):
    selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )
    existing = ImportMediaSessionDestination(
        selection=selection,
        import_root=selection.destination_path(tmp_path / "Photos_Master"),
    )
    session = ImportMediaSession(
        session_id="MPS-SESSION-STORED",
        destination=existing,
    )
    processor_calls = []
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "process_import_media_batch",
        lambda *args, **kwargs: processor_calls.append((args, kwargs)),
    )
    state_path = tmp_path / "active_session.json"
    original_state = b"unchanged active state"
    state_path.write_bytes(original_state)

    with pytest.raises(ValueError, match="requires"):
        run_import_media_session(
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="08-01_Ljubljana",
            session=session,
            session_state_path=state_path,
        )

    assert processor_calls == []
    assert session.destination is existing
    assert state_path.read_bytes() == original_state
    assert not existing.import_root.exists()


def test_matching_stored_structured_destination_reaches_processor(
    monkeypatch,
    tmp_path: Path,
):
    from types import SimpleNamespace

    selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )
    existing = ImportMediaSessionDestination(
        selection=selection,
        import_root=selection.destination_path(tmp_path / "Photos_Master"),
    )
    session = ImportMediaSession(destination=existing)
    processor_calls = []
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner.discover_import_media",
        lambda settings: ImportMediaSelection(
            sources=[_card(tmp_path / "reader", raw=1)]
        ),
    )

    def process(*args, **kwargs):
        processor_calls.append((args, kwargs))
        return SimpleNamespace(
            copied=0,
            failed=1,
            nothing_to_import=False,
            success=False,
        )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "process_import_media_batch",
        process,
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="08-01_Ljubljana",
        destination_selection=selection,
        session=session,
    )

    assert not result.success
    assert len(processor_calls) == 1
    assert session.destination is existing


def test_non_empty_legacy_session_rejects_structured_destination(
    monkeypatch,
    tmp_path: Path,
):
    session = ImportMediaSession(
        session_id="MPS-SESSION-LEGACY",
        source_fingerprints={"legacy-card"},
        processed_source_files=[tmp_path / "legacy-card" / "photo.ARW"],
    )
    processor_calls = []
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "process_import_media_batch",
        lambda *args, **kwargs: processor_calls.append((args, kwargs)),
    )
    state_path = tmp_path / "active_session.json"
    original_state = b"unchanged legacy state"
    state_path.write_bytes(original_state)
    original_fingerprints = session.source_fingerprints.copy()
    original_files = session.processed_source_files.copy()

    with pytest.raises(ValueError, match="non-empty legacy"):
        run_import_media_session(
            _settings(tmp_path),
            year=2026,
            project="Adriatic",
            day="08-01_Ljubljana",
            destination_selection=ImportDestinationSelection(
                year=2026,
                month_day="08-01",
                project="Adriatic",
                description="Ljubljana",
            ),
            session=session,
            session_state_path=state_path,
        )

    assert processor_calls == []
    assert session.destination is None
    assert session.source_fingerprints == original_fingerprints
    assert session.processed_source_files == original_files
    assert state_path.read_bytes() == original_state
    assert not (tmp_path / "Photos_Master").exists()


def test_failed_structured_batch_does_not_set_destination(
    monkeypatch,
    tmp_path: Path,
):
    from types import SimpleNamespace

    session = ImportMediaSession()
    state_path = tmp_path / "active_session.json"
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner.discover_import_media",
        lambda settings: ImportMediaSelection(
            sources=[_card(tmp_path / "reader", raw=1)]
        ),
    )
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner.process_import_media_batch",
        lambda *args, **kwargs: SimpleNamespace(
            copied=0,
            failed=1,
            nothing_to_import=False,
            success=False,
        ),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="08-01_Ljubljana",
        destination_selection=ImportDestinationSelection(
            year=2026,
            month_day="08-01",
            project="Adriatic",
            description="Ljubljana",
        ),
        session=session,
        session_state_path=state_path,
    )

    assert not result.success
    assert session.destination is None
    assert not state_path.exists()
