import json
import zipfile

import pytest

from tools.release_builder import ReleaseSpec, build_release


def _make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mps" / "services").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "mps" / "services" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "docs" / "Example.md").write_text("# Example\n", encoding="utf-8")
    return repo


def _spec():
    return ReleaseSpec(
        sprint="999.1",
        codename="Test Release",
        release="RC1",
        branch="test-branch",
        expected_tests=123,
        commit_message="Test commit message",
        payload_files=(
            "mps/services/example.py",
            "docs/Example.md",
        ),
    )


def test_release_builder_creates_zip_archive(tmp_path):
    repo = _make_repo(tmp_path)
    archive = build_release(repo, tmp_path / "out", _spec())

    assert archive.exists()
    assert archive.name == "Sprint_999_1_TestRelease_RC1.zip"


def test_release_builder_includes_standard_release_files(tmp_path):
    repo = _make_repo(tmp_path)
    archive = build_release(repo, tmp_path / "out", _spec())

    with zipfile.ZipFile(archive) as package:
        names = set(package.namelist())

    assert "Sprint_999_1_TestRelease_RC1/README_FIRST.txt" in names
    assert "Sprint_999_1_TestRelease_RC1/RELEASE_NOTES.md" in names
    assert "Sprint_999_1_TestRelease_RC1/CHANGES.md" in names
    assert "Sprint_999_1_TestRelease_RC1/COMMIT_MESSAGE.txt" in names
    assert "Sprint_999_1_TestRelease_RC1/release.json" in names
    assert "Sprint_999_1_TestRelease_RC1/apply.sh" in names
    assert "Sprint_999_1_TestRelease_RC1/verify.sh" in names
    assert "Sprint_999_1_TestRelease_RC1/rollback.sh" in names


def test_release_builder_copies_payload_files(tmp_path):
    repo = _make_repo(tmp_path)
    archive = build_release(repo, tmp_path / "out", _spec())

    with zipfile.ZipFile(archive) as package:
        content = package.read("Sprint_999_1_TestRelease_RC1/mps/services/example.py")

    assert content == b"VALUE = 1\n"


def test_release_builder_writes_release_metadata(tmp_path):
    repo = _make_repo(tmp_path)
    archive = build_release(repo, tmp_path / "out", _spec())

    with zipfile.ZipFile(archive) as package:
        data = json.loads(package.read("Sprint_999_1_TestRelease_RC1/release.json"))

    assert data["project"] == "Mac Photo Studio"
    assert data["sprint"] == "999.1"
    assert data["codename"] == "Test Release"
    assert data["expected_tests"] == 123
    assert data["commit_message"] == "Test commit message"


def test_release_builder_rejects_missing_payload_file(tmp_path):
    repo = _make_repo(tmp_path)
    spec = ReleaseSpec(
        sprint="999.2",
        codename="Broken Release",
        release="RC1",
        branch="test-branch",
        expected_tests=123,
        commit_message="Broken commit",
        payload_files=("missing/file.py",),
    )

    with pytest.raises(FileNotFoundError):
        build_release(repo, tmp_path / "out", spec)
