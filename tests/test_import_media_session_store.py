from pathlib import Path

from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_session_store import (
    load_import_media_session,
    save_import_media_session,
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
