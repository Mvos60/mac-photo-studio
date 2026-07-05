from __future__ import annotations

import logging
from datetime import datetime

from mps.constants import USER_LOG_DIR


def configure_logging() -> logging.Logger:
    USER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    log_file = USER_LOG_DIR / f"mac-photo-studio-{stamp}.log"

    logger = logging.getLogger("mac-photo-studio")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
