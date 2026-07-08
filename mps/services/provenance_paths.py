from pathlib import Path


def certificate_path(import_root: str | Path, certificate_id: str) -> Path:
    root = Path(import_root)

    return (
        root
        / "provenance"
        / f"{certificate_id}.json"
    )
