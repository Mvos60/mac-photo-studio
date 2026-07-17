from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise RuntimeError(
        "PyYAML is required. Install with: sudo apt install python3-yaml"
    ) from exc

from mps.constants import USER_CONFIG_DIR
from mps.exceptions import ConfigurationError


DEFAULT_SETTINGS = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "default_settings.yaml"
)


def expand_user_values(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("~"):
        return str(Path(value).expanduser())

    if isinstance(value, dict):
        return {
            key: expand_user_values(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            expand_user_values(item)
            for item in value
        ]

    return value


class Settings:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = expand_user_values(data)

    def get(
        self,
        dotted_key: str,
        default: Any = None,
    ) -> Any:
        current: Any = self.data

        for part in dotted_key.split("."):
            if (
                not isinstance(current, dict)
                or part not in current
            ):
                return default

            current = current[part]

        return current


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(
            path.read_text(encoding="utf-8")
        ) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML in {path}: {exc}"
        ) from exc

    return data


def load_settings(
    path: Path | None = None,
) -> Settings:
    if path is not None:
        return Settings(_load_yaml(path))

    user_settings = (
        USER_CONFIG_DIR
        / "settings.yaml"
    )

    if user_settings.exists():
        return Settings(
            _load_yaml(user_settings)
        )

    if DEFAULT_SETTINGS.exists():
        return Settings(
            _load_yaml(DEFAULT_SETTINGS)
        )

    raise ConfigurationError(
        "No configuration file found."
    )
