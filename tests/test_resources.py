from pathlib import Path

import pytest

from mps import resources


def test_asset_path_is_independent_of_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = resources.asset_path("branding/mps-camera-512.png")
    assert path.is_absolute()
    assert path.is_file()


def test_missing_asset_has_clear_error():
    with pytest.raises(
        resources.ResourceNotFoundError,
        match="Required Mac Photo Studio asset is missing",
    ):
        resources.asset_path("branding/not-present.png")


@pytest.mark.parametrize("value", ["/absolute.png", "../outside.png"])
def test_asset_path_rejects_paths_outside_package(value):
    with pytest.raises(ValueError, match="package-relative"):
        resources.asset_path(value)


def test_production_code_has_no_download_source_path():
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("mps").rglob("*.py")
    )
    assert "/home/mac/Downloads" not in production
