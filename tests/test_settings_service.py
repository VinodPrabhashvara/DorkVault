import json
import os

import pytest

from dorkvault.core.constants import (
    DEFAULT_BROWSER_BEHAVIOR,
    DEFAULT_RECENT_LIMIT,
    DEFAULT_THEME,
    THEME_DARK,
    THEME_LIGHT,
)
from dorkvault.core.exceptions import SettingsError
from dorkvault.core.models import AppSettings
from dorkvault.services.settings_service import SettingsService


def test_settings_service_creates_default_settings_file(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path=settings_path)

    settings = service.load()

    assert settings == AppSettings()
    assert json.loads(settings_path.read_text(encoding="utf-8")) == {
        "compact_view_enabled": True,
        "last_target": "",
        "open_in_browser_behavior": DEFAULT_BROWSER_BEHAVIOR,
        "recent_limit": DEFAULT_RECENT_LIMIT,
        "theme": DEFAULT_THEME,
        "window_geometry": None,
    }


def test_settings_service_persists_custom_settings(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path=settings_path)

    custom_settings = AppSettings(
        theme=THEME_DARK,
        open_in_browser_behavior="new_window",
        recent_limit=40,
        compact_view_enabled=False,
        last_target="example.com",
        window_geometry={"x": 120, "y": 80, "width": 1366, "height": 860},
    )
    service.save(custom_settings)

    reloaded_service = SettingsService(settings_path=settings_path)
    assert reloaded_service.load() == custom_settings


def test_settings_service_normalizes_invalid_payload_values(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "theme": "",
                "open_in_browser_behavior": "sideways",
                "recent_limit": "lots",
                "compact_view_enabled": "yes",
                "last_target": " example.org ",
                "window_geometry": {"x": "left", "y": 20, "width": 900, "height": 700},
                "favorites": ["legacy"],
                "recents": ["legacy"],
            }
        ),
        encoding="utf-8",
    )

    service = SettingsService(settings_path=settings_path)
    settings = service.load()

    assert settings.theme == DEFAULT_THEME
    assert settings.open_in_browser_behavior == DEFAULT_BROWSER_BEHAVIOR
    assert settings.recent_limit == DEFAULT_RECENT_LIMIT
    assert settings.compact_view_enabled is True
    assert settings.last_target == "example.org"
    assert settings.window_geometry is None


def test_settings_service_resets_invalid_json_and_logs_warning(tmp_path, caplog) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{ invalid json", encoding="utf-8")

    service = SettingsService(settings_path=settings_path)
    settings = service.load()

    assert settings == AppSettings()
    assert "invalid JSON" in caplog.text


def test_settings_service_raises_settings_error_when_save_replace_fails(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path=settings_path)

    def _raise_replace(_src: str, _dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", _raise_replace)

    with pytest.raises(SettingsError, match="could not be saved"):
        service.save(AppSettings())


def test_settings_service_available_themes_are_light_and_dark(tmp_path) -> None:
    service = SettingsService(settings_path=tmp_path / "settings.json")

    assert service.available_themes() == [THEME_LIGHT, THEME_DARK]
