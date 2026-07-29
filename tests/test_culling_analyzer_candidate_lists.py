from pathlib import Path

from mps.services.culling_analyzer import (
    CullingAnalysis,
    MissingImportedJpeg,
)


def test_orphan_raw_candidates_are_not_duplicated(
    tmp_path: Path,
):
    raw = tmp_path / "MAC00001.ARW"
    raw.write_bytes(b"raw")

    item = MissingImportedJpeg(
        stem="MAC00001",
        jpeg_path=tmp_path / "MAC00001.JPG",
        jpeg_provenance_id="jpeg-prov",
        jpeg_sha256="jpeg-sha",
        raw_path=raw,
        raw_provenance_id="raw-prov",
        raw_sha256="raw-sha",
        raw_hash_matches=True,
    )

    analysis = CullingAnalysis(
        import_root=tmp_path,
        missing_jpegs=[item],
    )

    assert analysis.orphan_raw_candidates == [item]
