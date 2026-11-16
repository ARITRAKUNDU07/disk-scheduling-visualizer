"""Thread-safe Audit Logging Subsystem for OSRM.

Configures a centralized logging pipeline writing to logs/activity.log with
the exact format: 'YYYY-MM-DD HH:MM:SS | LEVEL | module | message'.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_INITIALIZED = False
_LOG_FILE_PATH: Optional[Path] = None


def get_logger(module_name: str) -> logging.Logger:
    """Retrieve or initialize a logger instance scoped to a specific module."""
    global _INITIALIZED, _LOG_FILE_PATH

    if not _INITIALIZED:
        init_logging()

    return logging.getLogger(module_name)


def init_logging(log_dir: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> Path:
    """Initialize root loggers, file handlers, and directory trees."""
    global _INITIALIZED, _LOG_FILE_PATH

    if log_dir is None:
        # Resolve project root relative to this file
        project_root = Path(__file__).resolve().parent.parent
        resolved_log_dir = project_root / "logs"
    else:
        resolved_log_dir = Path(log_dir).resolve()

    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    _LOG_FILE_PATH = resolved_log_dir / "activity.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if re-initialized
    if not root_logger.handlers:
        file_handler = logging.FileHandler(str(_LOG_FILE_PATH), mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _INITIALIZED = True
    return _LOG_FILE_PATH


def log_event(module: str, message: str, level: str = "INFO", exc_info: Optional[Exception] = None) -> None:
    """Convenience helper to record structured events with timestamp and severity."""
    logger = get_logger(module)
    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.log(lvl, message, exc_info=exc_info if lvl <= logging.DEBUG or exc_info else None)
