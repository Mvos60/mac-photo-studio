from __future__ import annotations

from pathlib import Path


APP_NAME = "mac-photo-studio"

HOME_DIR = Path.home()

USER_CONFIG_DIR = HOME_DIR / ".config" / APP_NAME
USER_STATE_DIR = HOME_DIR / ".local" / "state" / APP_NAME
USER_CACHE_DIR = HOME_DIR / ".cache" / APP_NAME

USER_LOG_DIR = USER_STATE_DIR / "logs"
LOG_DIR = USER_LOG_DIR

ACTIVE_IMPORT_SESSION = (
    USER_STATE_DIR
    / "active_import_session.json"
)

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

DEFAULT_SETTINGS_FILE = (
    PROJECT_ROOT
    / "config"
    / "default_settings.yaml"
)
