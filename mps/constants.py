from pathlib import Path

APP_NAME = "Mac Photo Studio"
APP_ID = "mac-photo-studio"

USER_CONFIG_DIR = Path.home() / ".config" / APP_ID
USER_STATE_DIR = Path.home() / ".local" / "state" / APP_ID
USER_LOG_DIR = USER_STATE_DIR / "logs"
DEFAULT_PHOTOS_ROOT = Path.home() / "Photos_Master"
