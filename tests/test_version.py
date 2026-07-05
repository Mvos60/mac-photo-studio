from mps.version import get_version


def test_version_is_alpha3():
    assert get_version() == "0.1.0-alpha3"
