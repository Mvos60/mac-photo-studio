from pathlib import Path
import json

import pytest

from mps.models.import_destination_selection import ImportDestinationSelection
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)
from mps.services.import_media_session_store import (
    load_import_media_session,
    save_import_media_session,
)


def _destination(
    tmp_path: Path,
    *,
    description: str = "Ljubljana",
) -> ImportMediaSessionDestination:
    selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description=description,
    )
    return ImportMediaSessionDestination(
        selection=selection,
        import_root=selection.destination_path(tmp_path / "Photos_Master"),
    )


def test_save_import_media_session_writes_state(
    tmp_path: Path,
):
    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
        source_fingerprints={
            "fingerprint-b",
            "fingerprint-a",
        },
        processed_source_files=[
            Path("/media/card/DSC0001.ARW"),
            Path("/media/card/DSC0001.JPG"),
        ],
    )

    output = save_import_media_session(
        session,
        tmp_path / "session.json",
    )

    assert output.exists()

    text = output.read_text(encoding="utf-8")

    assert "MPS-SESSION-1" in text
    assert "fingerprint-a" in text
    assert "fingerprint-b" in text
    assert "DSC0001.ARW" in text
    assert "DSC0001.JPG" in text


def test_load_import_media_session_restores_state(
    tmp_path: Path,
):
    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
        source_fingerprints={
            "fingerprint-raw",
            "fingerprint-jpeg",
        },
        processed_source_files=[
            Path("/media/card/DSC0001.ARW"),
            Path("/media/card/DSC0001.JPG"),
        ],
    )

    path = save_import_media_session(
        session,
        tmp_path / "session.json",
    )

    loaded = load_import_media_session(path)

    assert loaded.session_id == "MPS-SESSION-1"
    assert loaded.sources == []
    assert loaded.source_fingerprints == {
        "fingerprint-raw",
        "fingerprint-jpeg",
    }
    assert loaded.processed_source_files == [
        Path("/media/card/DSC0001.ARW"),
        Path("/media/card/DSC0001.JPG"),
    ]


def test_loaded_session_still_prevents_known_fingerprint():
    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
        source_fingerprints={
            "known-card",
        },
    )

    assert session.add_source(
        source=None,
        fingerprint="known-card",
    ) is False


def test_structured_destination_is_saved_as_exact_json(tmp_path: Path):
    path = save_import_media_session(
        ImportMediaSession(
            session_id="MPS-SESSION-STRUCTURED",
            destination=_destination(tmp_path),
        ),
        tmp_path / "session.json",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["destination"] == {
        "year": 2026,
        "month_day": "08-01",
        "project": "Adriatic",
        "description": "Ljubljana",
        "import_root": str(
            tmp_path / "Photos_Master" / "2026" / "08"
            / "01_Ljubljana" / "Adriatic"
        ),
    }


@pytest.mark.parametrize("description", ["Ljubljana", ""])
def test_structured_destination_round_trips(
    tmp_path: Path,
    description: str,
):
    destination = _destination(tmp_path, description=description)
    path = save_import_media_session(
        ImportMediaSession(destination=destination),
        tmp_path / "session.json",
    )
    loaded = load_import_media_session(path)
    assert loaded.destination == destination
    assert loaded.destination is not None
    assert loaded.destination.selection.description == description
    assert isinstance(loaded.destination.import_root, Path)


def test_legacy_json_loads_without_destination(tmp_path: Path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps({"session_id": "MPS-SESSION-LEGACY"}),
        encoding="utf-8",
    )
    loaded = load_import_media_session(path)
    assert loaded.session_id == "MPS-SESSION-LEGACY"
    assert loaded.sources == []
    assert loaded.source_fingerprints == set()
    assert loaded.processed_source_files == []
    assert loaded.destination is None


def test_saving_legacy_session_omits_destination(tmp_path: Path):
    path = save_import_media_session(
        ImportMediaSession(session_id="MPS-SESSION-LEGACY"),
        tmp_path / "session.json",
    )
    assert "destination" not in json.loads(
        path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    "missing_field",
    ["year", "month_day", "project", "description", "import_root"],
)
def test_destination_rejects_each_missing_field(
    tmp_path: Path,
    missing_field: str,
):
    destination = {
        "year": 2026,
        "month_day": "08-01",
        "project": "Adriatic",
        "description": "Ljubljana",
        "import_root": str(tmp_path / "Photos_Master"),
    }
    del destination[missing_field]
    path = tmp_path / "session.json"
    path.write_text(
        json.dumps({"destination": destination}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing"):
        load_import_media_session(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("year", True),
        ("month_day", "02-30"),
        ("project", "Unsafe/Project"),
        ("description", "Unsafe/Description"),
        ("import_root", 123),
    ],
)
def test_destination_rejects_invalid_nested_values(
    tmp_path: Path,
    field: str,
    value: object,
):
    destination = {
        "year": 2026,
        "month_day": "08-01",
        "project": "Adriatic",
        "description": "Ljubljana",
        "import_root": str(tmp_path / "Photos_Master"),
    }
    destination[field] = value
    path = tmp_path / "session.json"
    path.write_text(
        json.dumps({"destination": destination}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_import_media_session(path)
