from mps.version import get_version


def test_version_is_current_release():
    assert get_version() == "0.2.0"
