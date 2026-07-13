from mps.services.provenance_event_paths import (
    event_directory,
    event_path,
)


def test_event_directory_uses_provenance_id():
    path = event_directory(
        "/photos/2026/Adriatic/03_Slovenia",
        "MPS-PROV-1234",
    )

    assert path.name == "MPS-PROV-1234"
    assert path.parent.name == "events"
    assert path.parent.parent.name == "provenance"


def test_event_path_uses_event_id():
    path = event_path(
        "/photos/2026/Adriatic/03_Slovenia",
        "MPS-PROV-1234",
        "MPS-EVENT-5678",
    )

    assert path.name == "MPS-EVENT-5678.json"
    assert path.parent.name == "MPS-PROV-1234"
    assert path.parent.parent.name == "events"
