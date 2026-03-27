"""Helpers for loading bundled text resources such as icons."""

from __future__ import annotations

import logging
from pathlib import Path

from dorkvault.core.constants import APP_NAME
from dorkvault.utils.paths import get_icon_path

logger = logging.getLogger(APP_NAME)


def read_text_resource(path: Path, *, default: str = "") -> str:
    """Read a text asset safely and return a fallback value on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "Unable to read text resource.",
            extra={
                "event": "resource_read_failed",
                "resource_path": str(path),
                "error": str(exc),
            },
        )
        return default


def resolve_icon_path(icon_name: str, *, fallback_name: str | None = "app_icon.svg") -> Path | None:
    """Resolve an icon asset path with an optional fallback icon."""
    primary_path = get_icon_path(icon_name)
    if primary_path.exists():
        return primary_path

    if fallback_name:
        fallback_path = get_icon_path(fallback_name)
        if fallback_path.exists():
            logger.warning(
                "Icon asset is missing. Falling back to the default icon.",
                extra={
                    "event": "icon_fallback_used",
                    "icon_name": icon_name,
                    "fallback_name": fallback_name,
                },
            )
            return fallback_path

    logger.warning(
        "Icon asset is missing and no fallback is available.",
        extra={
            "event": "icon_missing",
            "icon_name": icon_name,
            "fallback_name": fallback_name or "",
        },
    )
    return None


def load_icon(icon_name: str, *, fallback_name: str | None = "app_icon.svg"):
    """Load a Qt icon from bundled assets with a safe fallback chain."""
    from PySide6.QtGui import QIcon

    resolved_path = resolve_icon_path(icon_name, fallback_name=fallback_name)
    if resolved_path is None:
        return QIcon()
    return QIcon(str(resolved_path))
