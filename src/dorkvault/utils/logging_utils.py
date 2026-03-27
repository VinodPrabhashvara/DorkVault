"""Logging configuration helpers."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dorkvault.core.constants import APP_NAME, LOG_FILE_NAME
from dorkvault.utils.paths import get_user_data_dir

_CONFIGURED_HANDLER_NAMES = {
    f"{APP_NAME.lower()}_console",
    f"{APP_NAME.lower()}_file",
}
_RESERVED_RECORD_KEYS = frozenset(logging.makeLogRecord({}).__dict__)


class StructuredFormatter(logging.Formatter):
    """Append non-standard log record fields as lightweight structured context."""

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)
        context_parts: list[str] = []

        for key, value in sorted(record.__dict__.items()):
            if key in _RESERVED_RECORD_KEYS or key.startswith("_"):
                continue
            context_parts.append(f"{key}={self._serialize_value(value)}")

        if not context_parts:
            return formatted_message
        return f"{formatted_message} | {' '.join(context_parts)}"

    @staticmethod
    def _serialize_value(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)) or value is None:
            return str(value)
        try:
            return json.dumps(value, ensure_ascii=True, sort_keys=True)
        except TypeError:
            return repr(value)


def configure_logging() -> logging.Logger:
    """Configure console and file logging once for the application."""
    root_logger = logging.getLogger()
    existing_handler_names = {handler.get_name() for handler in root_logger.handlers}
    if _CONFIGURED_HANDLER_NAMES.issubset(existing_handler_names):
        return logging.getLogger(APP_NAME)

    formatter = StructuredFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.set_name(f"{APP_NAME.lower()}_console")
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    log_path = get_user_data_dir() / LOG_FILE_NAME
    file_handler = _build_file_handler(log_path, formatter)
    if file_handler is not None:
        root_logger.addHandler(file_handler)

    logging.getLogger(APP_NAME).setLevel(logging.INFO)
    logging.getLogger("PySide6").setLevel(logging.WARNING)
    logging.captureWarnings(True)
    return logging.getLogger(APP_NAME)


def _build_file_handler(log_path: Path, formatter: logging.Formatter) -> RotatingFileHandler | None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_path, maxBytes=512_000, backupCount=3, encoding="utf-8")
    except OSError as exc:
        logging.getLogger(APP_NAME).warning(
            "File logging could not be enabled.",
            extra={
                "event": "log_file_unavailable",
                "log_path": str(log_path),
                "error": str(exc),
            },
        )
        return None

    handler.set_name(f"{APP_NAME.lower()}_file")
    handler.setFormatter(formatter)
    return handler
