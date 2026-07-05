from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


def deep_merge(defaults: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing)
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value
        elif isinstance(default_value, dict) and isinstance(result[key], dict):
            result[key] = deep_merge(default_value, result[key])
    return result


def main() -> int:
    default_path = Path(sys.argv[1])
    settings_path = Path(sys.argv[2])

    defaults = yaml.safe_load(default_path.read_text(encoding="utf-8")) or {}
    existing = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}

    merged = deep_merge(defaults, existing)
    settings_path.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
