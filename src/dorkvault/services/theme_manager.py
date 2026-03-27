"""Theme loading and runtime application helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from dorkvault.core.constants import APP_NAME, DEFAULT_THEME, THEME_DARK, THEME_LIGHT, THEME_OPTIONS
from dorkvault.utils.paths import get_assets_dir
from dorkvault.utils.resource_loader import read_text_resource


class ThemeManager:
    """Load, validate, and apply the two supported application themes."""

    _THEME_FILES = {
        THEME_LIGHT: "light.qss",
        THEME_DARK: "dark.qss",
    }

    def __init__(self, themes_dir: Path | None = None) -> None:
        self.logger = logging.getLogger(APP_NAME)
        self.themes_dir = themes_dir or (get_assets_dir() / "themes")

    def available_themes(self) -> list[str]:
        return list(THEME_OPTIONS)

    def is_valid_theme(self, theme_name: str) -> bool:
        return theme_name.strip().lower() in THEME_OPTIONS

    def normalize_theme_name(self, theme_name: str | None) -> str:
        normalized = (theme_name or "").strip().lower()
        if normalized in THEME_OPTIONS:
            return normalized
        return DEFAULT_THEME

    def theme_path(self, theme_name: str) -> Path:
        normalized = self.normalize_theme_name(theme_name)
        return self.themes_dir / self._THEME_FILES[normalized]

    def load_theme(self, theme_name: str | None = None) -> str:
        normalized = self.normalize_theme_name(theme_name)
        theme_path = self.theme_path(normalized)
        if not theme_path.exists():
            if normalized != DEFAULT_THEME:
                self.logger.warning(
                    "Theme asset is missing. Falling back to the default theme.",
                    extra={
                        "event": "theme_fallback_used",
                        "theme_name": normalized,
                        "fallback_name": DEFAULT_THEME,
                    },
                )
                return self.load_theme(DEFAULT_THEME)
            self.logger.warning(
                "The default theme asset is missing.",
                extra={
                    "event": "default_theme_missing",
                    "theme_name": DEFAULT_THEME,
                    "theme_path": str(theme_path),
                },
            )
            return ""
        return read_text_resource(theme_path, default="")

    def apply_theme(self, application, theme_name: str | None = None) -> str:  # noqa: ANN001
        normalized = self.normalize_theme_name(theme_name)
        application.setProperty("dorkvaultTheme", normalized)
        application.setStyleSheet(self.load_theme(normalized))
        return normalized
