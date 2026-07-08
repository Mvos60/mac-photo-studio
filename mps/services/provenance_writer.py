from pathlib import Path

from mps.models.provenance_certificate import ProvenanceCertificate


def write_certificate(
    certificate: ProvenanceCertificate,
    output_path: str | Path,
) -> Path:
    output = Path(output_path)

    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        certificate.to_json(),
        encoding="utf-8",
    )

    return output


def write_certificate_for_import(
    certificate: ProvenanceCertificate,
    import_root: str | Path,
) -> Path:
    from mps.services.provenance_paths import certificate_path

    output_path = certificate_path(
        import_root,
        certificate.certificate_id,
    )

    return write_certificate(certificate, output_path)
