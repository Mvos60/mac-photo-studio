from pathlib import Path


def index_path(import_root: str | Path) -> Path:
    return Path(import_root) / "provenance" / "certificate_index.json"
