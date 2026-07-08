from pathlib import Path

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
)


def write_index(
    index: ProvenanceCertificateIndex,
    output_path: str | Path,
) -> Path:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        index.to_json(),
        encoding="utf-8",
    )

    return output
