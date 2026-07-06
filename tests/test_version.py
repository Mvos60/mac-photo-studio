from mps.version import get_version


def test_version_is_current_dev():
    assert get_version() == "0.2.0-dev"
