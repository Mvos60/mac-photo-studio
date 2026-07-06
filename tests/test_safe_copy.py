from pathlib import Path

from mps.services.safe_copy import copy_one_file, sha256_file


def test_copy_one_file_success(tmp_path: Path):
    source = tmp_path / "source" / "DSC0001.ARW"
    destination = tmp_path / "destination" / "DSC0001.ARW"

    source.parent.mkdir()
    source.write_bytes(b"photograph-data")

    result = copy_one_file(source, destination)

    assert result.success
    assert destination.exists()
    assert destination.read_bytes() == b"photograph-data"
    assert result.size_bytes == len(b"photograph-data")
    assert result.checksum == sha256_file(source)


def test_copy_one_file_creates_parent_directory(tmp_path: Path):
    source = tmp_path / "DSC0001.ARW"
    destination = tmp_path / "nested" / "folder" / "DSC0001.ARW"

    source.write_bytes(b"raw")

    result = copy_one_file(source, destination)

    assert result.success
    assert destination.exists()


def test_copy_one_file_refuses_overwrite(tmp_path: Path):
    source = tmp_path / "source.ARW"
    destination = tmp_path / "destination.ARW"

    source.write_bytes(b"new")
    destination.write_bytes(b"existing")

    result = copy_one_file(source, destination)

    assert not result.success
    assert destination.read_bytes() == b"existing"
    assert "refusing to overwrite" in result.message


def test_copy_one_file_missing_source_fails_safely(tmp_path: Path):
    source = tmp_path / "missing.ARW"
    destination = tmp_path / "destination.ARW"

    result = copy_one_file(source, destination)

    assert not result.success
    assert not destination.exists()
    assert "does not exist" in result.message
