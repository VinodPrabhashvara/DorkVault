"""Persistence for user settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dorkvault.core.constants import APP_NAME, DEFAULT_THEME
from dorkvault.core.exceptions import SettingsError
from dorkvault.core.models import AppSettings
from dorkvault.services.theme_manager import ThemeManager
from dorkvault.utils.json_storage import write_json_atomic
from dorkvault.utils.paths import get_user_data_dir


class SettingsService:
    """Load and save application settings in the user's roaming profile."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self.logger = logging.getLogger(APP_NAME)
        self.settings_path = settings_path or (get_user_data_dir() / "settings.json")
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.theme_manager = ThemeManager()
        self._settings: AppSettings | None = None

    @property
    def settings(self) -> AppSettings:
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            default_settings = AppSettings()
            self.logger.info(
                "No settings file found. Using defaults.",
                extra={
                    "event": "settings_default_created",
                    "settings_path": str(self.settings_path),
                },
            )
            try:
                self.save(default_settings)
            except SettingsError:
                self.logger.exception(
                    "Default settings could not be written.",
                    extra={
                        "event": "settings_default_save_failed",
                        "settings_path": str(self.settings_path),
                    },
                )
                self._settings = default_settings
            return default_settings

        try:
            with self.settings_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self.logger.warning(
                "Settings file contains invalid JSON. Resetting to defaults.",
                extra={
                    "event": "settings_invalid_json",
                    "settings_path": str(self.settings_path),
                    "error": str(exc),
                },
            )
            return self._reset_to_defaults()
        except OSError as exc:
            self.logger.warning(
                "Settings file could not be read. Using defaults in memory.",
                extra={
                    "event": "settings_read_failed",
                    "settings_path": str(self.settings_path),
                    "error": str(exc),
                },
            )
            default_settings = AppSettings()
            self._settings = default_settings
            return default_settings

        if not isinstance(payload, dict):
            self.logger.warning(
                "Settings payload is not an object. Resetting to defaults.",
                extra={
                    "event": "settings_invalid_payload",
                    "settings_path": str(self.settings_path),
                    "payload_type": type(payload).__name__,
                },
            )
            return self._reset_to_defaults()

        loaded_settings = AppSettings.from_dict(payload)
        normalized_theme = self.theme_manager.normalize_theme_name(loaded_settings.theme)
        if (
            normalized_theme != loaded_settings.theme
            or not self.theme_manager.theme_path(normalized_theme).exists()
        ):
            self.logger.info(
                "Saved theme is invalid or unavailable. Falling back to the default theme.",
                extra={
                    "event": "settings_theme_normalized",
                    "requested_theme": loaded_settings.theme,
                    "fallback_theme": DEFAULT_THEME,
                },
            )
            loaded_settings.theme = normalized_theme
        self._settings = loaded_settings
        self.logger.info(
            "Loaded application settings.",
            extra={
                "event": "settings_loaded",
                "settings_path": str(self.settings_path),
                "theme": loaded_settings.theme,
                "recent_limit": loaded_settings.recent_limit,
                "compact_view_enabled": loaded_settings.compact_view_enabled,
            },
        )
        return loaded_settings

    def save(self, settings: AppSettings | None = None) -> None:
        active_settings = settings or self.settings
        try:
            write_json_atomic(self.settings_path, active_settings.to_dict())
        except OSError as exc:
            self.logger.exception(
                "Settings could not be saved.",
                extra={
                    "event": "settings_save_failed",
                    "settings_path": str(self.settings_path),
                    "error": str(exc),
                },
            )
            self._settings = active_settings if self._settings is None else self._settings
            raise SettingsError("Settings could not be saved.") from exc

        self._settings = active_settings
        self.logger.info(
            "Saved application settings.",
            extra={
                "event": "settings_saved",
                "settings_path": str(self.settings_path),
                "theme": active_settings.theme,
                "recent_limit": active_settings.recent_limit,
                "compact_view_enabled": active_settings.compact_view_enabled,
            },
        )

    def update(self, settings: AppSettings) -> AppSettings:
        self.save(settings)
        return self.settings

    def update_last_target(self, target: str) -> None:
        self.settings.last_target = target.strip()
        self.save()

    def available_themes(self) -> list[str]:
        return self.theme_manager.available_themes()

    def _reset_to_defaults(self) -> AppSettings:
        default_settings = AppSettings()
        try:
            self.save(default_settings)
        except SettingsError:
            self.logger.exception(
                "Default settings could not be restored after a load failure.",
                extra={
                    "event": "settings_reset_failed",
                    "settings_path": str(self.settings_path),
                },
            )
            self._settings = default_settings
        return default_settings
