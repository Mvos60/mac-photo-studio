from pathlib import Path

from mps.models.provenance_certificate import ProvenanceCertificate
from mps.services.provenance_certificate import create_certificate
from mps.services.provenance_writer import write_certificate_for_import


def create_and_write_certificate(
    *,
    import_root: str | Path,
    session_id: str,
    source_path: str,
    destination_path: str,
    sha256: str,
    camera_model: str,
    manifest_path: str,
) -> tuple[ProvenanceCertificate, Path]:
    certificate = create_certificate(
        session_id=session_id,
        source_path=source_path,
        destination_path=destination_path,
        sha256=sha256,
        camera_model=camera_model,
        manifest_path=manifest_path,
    )

    written_path = write_certificate_for_import(
        certificate,
        import_root,
    )

    return certificate, written_path
