from mps.services.duplicate_detector import check_duplicate


def test_duplicate_detector_reports_missing_destination(tmp_path):
    source = tmp_path / "source.ARW"
    destination = tmp_path / "destination.ARW"

    source.write_bytes(b"photo data")

    result = check_duplicate(source, destination)

    assert result.exists is False
    assert result.identical is False
    assert result.conflict is False


def test_duplicate_detector_reports_identical_files(tmp_path):
    source = tmp_path / "source.ARW"
    destination = tmp_path / "destination.ARW"

    source.write_bytes(b"same photo data")
    destination.write_bytes(b"same photo data")

    result = check_duplicate(source, destination)

    assert result.exists is True
    assert result.identical is True
    assert result.conflict is False


def test_duplicate_detector_reports_conflicting_files(tmp_path):
    source = tmp_path / "source.ARW"
    destination = tmp_path / "destination.ARW"

    source.write_bytes(b"original photo data")
    destination.write_bytes(b"different photo data")

    result = check_duplicate(source, destination)

    assert result.exists is True
    assert result.identical is False
    assert result.conflict is True


def test_duplicate_detector_handles_large_files(tmp_path):
    source = tmp_path / "source.ARW"
    destination = tmp_path / "destination.ARW"

    data = b"mac-photo-studio" * 150000  # ~2.4 MB

    source.write_bytes(data)
    destination.write_bytes(data)

    result = check_duplicate(source, destination)

    assert result.exists is True
    assert result.identical is True
    assert result.conflict is False
