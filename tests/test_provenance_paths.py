from mps.services.provenance_paths import certificate_path


def test_certificate_path():
    path = certificate_path(
        "/photos/2026/07/08",
        "MPS-CERT-1234",
    )

    assert path.name == "MPS-CERT-1234.json"
    assert path.parent.name == "provenance"
