from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise RuntimeError("PyYAML is required. Install with: sudo apt install python3-yaml") from exc

from mps.constants import USER_CONFIG_DIR
from mps.exceptions import ConfigurationError


def expand_user_values(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("~"):
        return str(Path(value).expanduser())
    if isinstance(value, dict):
        return {k: expand_user_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_user_values(v) for v in value]
    return value


class Settings:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = expand_user_values(data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        current: Any = self.data
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or USER_CONFIG_DIR / "settings.yaml"
    if not config_path.exists():
        raise ConfigurationError(f"Settings file not found: {config_path}")

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {exc}") from exc

    return Settings(data)
