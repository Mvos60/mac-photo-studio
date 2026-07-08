from mps.services.provenance_index_paths import index_path


def test_index_path():
    path = index_path("/photos/import_001")

    assert path.name == "certificate_index.json"
    assert path.parent.name == "provenance"
