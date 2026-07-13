from mps.services.safe_copy import sha256_file
from mps.services.stable_file_hash import stable_file_sha256


def test_stable_file_sha256_hashes_unchanged_file(tmp_path):
    photo = tmp_path / "photo.tif"
    photo.write_bytes(b"stable photograph")

    result = stable_file_sha256(photo)

    assert result.stable is True
    assert result.path == photo
    assert result.sha256 == sha256_file(photo)
    assert result.errors == ()


def test_stable_file_sha256_rejects_missing_file(tmp_path):
    photo = tmp_path / "missing.tif"

    result = stable_file_sha256(photo)

    assert result.stable is False
    assert result.sha256 is None
    assert result.errors == (
        "File does not exist",
    )


def test_stable_file_sha256_rejects_directory(tmp_path):
    output = tmp_path / "output"
    output.mkdir()

    result = stable_file_sha256(output)

    assert result.stable is False
    assert result.sha256 is None
    assert result.errors == (
        "Path is not a file",
    )


def test_stable_file_sha256_detects_content_change(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "photo.tif"
    photo.write_bytes(b"first photograph")

    from mps.services import stable_file_hash

    original_sha256_file = stable_file_hash.sha256_file
    call_count = 0

    def changing_sha256_file(path):
        nonlocal call_count

        call_count += 1
        checksum = original_sha256_file(path)

        if call_count == 1:
            path.write_bytes(b"changed photograph")

        return checksum

    monkeypatch.setattr(
        stable_file_hash,
        "sha256_file",
        changing_sha256_file,
    )

    result = stable_file_sha256(photo)

    assert result.stable is False
    assert result.sha256 is None
    assert result.errors == (
        "File changed while SHA-256 was being calculated",
    )
