"""Filesystem path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dorkvault.core.constants import APP_NAME


def get_package_root() -> Path:
    """Return the source package root for the installed module."""
    return Path(__file__).resolve().parents[1]


def get_project_root() -> Path:
    """Return the repository root during development."""
    return Path(__file__).resolve().parents[3]


def is_packaged_app() -> bool:
    """Return whether the application is running from a frozen bundle."""
    return bool(getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None))


def get_runtime_root() -> Path:
    """Return the active runtime root for development or packaged execution."""
    if is_packaged_app():
        return Path(str(getattr(sys, "_MEIPASS")))
    return get_project_root()


def get_runtime_package_root() -> Path:
    """Return the package root that contains bundled data and assets."""
    if is_packaged_app():
        bundled_package_root = get_runtime_root() / "dorkvault"
        if bundled_package_root.exists():
            return bundled_package_root
    return get_package_root()


def get_data_dir() -> Path:
    """Return the directory that stores bundled data files."""
    return get_runtime_package_root() / "data"


def get_assets_dir() -> Path:
    """Return the directory that stores bundled UI assets."""
    return get_runtime_package_root() / "assets"


def get_icon_path(icon_name: str) -> Path:
    """Return the path for a named icon asset."""
    return get_assets_dir() / "icons" / icon_name


def get_theme_path(theme_name: str) -> Path:
    """Return the path for a named QSS theme asset."""
    return get_assets_dir() / "themes" / theme_name


def get_user_data_dir() -> Path:
    """Return the writable per-user application data directory."""
    base_dir = os.environ.get("APPDATA")
    if base_dir:
        return Path(base_dir) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def get_user_techniques_dir() -> Path:
    """Return the writable per-user techniques directory."""
    return get_user_data_dir() / "techniques"
