from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QRect, Qt

PySide6_QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = PySide6_QtWidgets.QApplication

from dorkvault.core.config import DEFAULT_APP_CONFIG
from dorkvault.core.models import AppSettings, Technique
from dorkvault.services.settings_service import SettingsService
from dorkvault.ui.main_window import MainWindow


def _create_window(tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings_service = SettingsService()
    window = MainWindow(settings_service=settings_service)
    window.show()
    qapp.processEvents()
    return window


def test_main_window_starts_with_all_techniques_visible(qapp: QApplication, tmp_path: Path, monkeypatch) -> None:
    window = _create_window(tmp_path, qapp, monkeypatch)

    try:
        available_geometry = window._startup_screen().availableGeometry()
        expected_width = min(
            available_geometry.width(),
            max(window._safe_minimum_width(available_geometry), int(available_geometry.width() * 0.88)),
        )
        expected_height = min(
            available_geometry.height(),
            max(window._safe_minimum_height(available_geometry), int(available_geometry.height() * 0.88)),
        )
        assert window.width() == expected_width
        assert window.height() == expected_height
        assert window.minimumWidth() == window._safe_minimum_width(available_geometry)
        assert window.minimumHeight() == window._safe_minimum_height(available_geometry)
        assert window.windowFlags() & Qt.WindowType.Window
        assert window.windowFlags() & Qt.WindowType.WindowTitleHint
        assert window.windowFlags() & Qt.WindowType.WindowSystemMenuHint
        assert window.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
        assert window.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint
        assert window.windowFlags() & Qt.WindowType.WindowCloseButtonHint
        assert not window.windowIcon().isNull()
        assert len(window._visible_techniques) == len(window.repository.all_techniques())
        assert window.technique_list.count_label.text().startswith("Showing all ")
        assert window.current_technique is not None
    finally:
        window.close()
        qapp.processEvents()


def test_main_window_supports_release_smoke_interactions(
    qapp: QApplication,
    tmp_path: Path,
    monkeypatch,
) -> None:
    window = _create_window(tmp_path, qapp, monkeypatch)

    try:
        window.target_toolbar.set_target_text("example.com")
        qapp.processEvents()

        window.target_toolbar.set_search_text("workflow")
        window._apply_filters()
        qapp.processEvents()
        assert window._visible_techniques
        assert any("workflow" in technique.search_text() for technique in window._visible_techniques)

        window.target_toolbar.set_search_text("")
        window.sidebar.select_category("GitHub Search")
        qapp.processEvents()
        assert window._visible_techniques
        assert all(technique.category == "GitHub Search" for technique in window._visible_techniques)

        selected_technique = window._visible_techniques[0]
        window._focus_technique(selected_technique.id)
        qapp.processEvents()
        assert window.current_technique is not None
        assert window.current_technique.id == selected_technique.id
        assert "example.com" in window.detail_panel.query_preview.toPlainText()
        assert window.detail_panel.title_label.text() == selected_technique.name

        window._copy_current_query()
        qapp.processEvents()
        assert "example.com" in QApplication.clipboard().text()

        launched: dict[str, str] = {}

        def _fake_launch(technique: Technique, target: str, *, open_behavior: str = "new_tab") -> str:
            launched["technique_id"] = technique.id
            launched["target"] = target
            launched["open_behavior"] = open_behavior
            return "https://example.test/search?q=ok"

        monkeypatch.setattr(window.launcher, "launch", _fake_launch)
        window._launch_current_technique()
        qapp.processEvents()
        assert launched == {
            "technique_id": selected_technique.id,
            "target": "example.com",
            "open_behavior": "new_tab",
        }

        def _fake_editor(existing_technique: Technique | None = None) -> Technique | None:
            assert existing_technique is None
            return window.custom_technique_service.create_custom_technique(
                {
                    "name": "Release Smoke Custom Technique",
                    "category": "GitHub Search",
                    "engine": "GitHub",
                    "description": "Created during the main-window release smoke test.",
                    "query_template": "org:{company} path:.github/workflows",
                    "variables": "company",
                    "tags": "release, smoke",
                    "example": "org:example path:.github/workflows",
                },
                existing_ids=[technique.id for technique in window.repository.all_techniques()],
            )

        monkeypatch.setattr(window, "_open_custom_technique_editor", _fake_editor)
        window._create_custom_technique()
        qapp.processEvents()
        assert window.current_technique is not None
        assert window.current_technique.id == "github-search-release-smoke-custom-technique"

        window.resize(DEFAULT_APP_CONFIG.minimum_width, DEFAULT_APP_CONFIG.minimum_height)
        qapp.processEvents()
        assert window.sidebar.width() >= window.sidebar.minimumWidth()
        assert window.technique_list.width() >= window.technique_list.minimumWidth()
        assert window.detail_panel.width() >= window.detail_panel.minimumWidth()
        assert window.detail_panel.content_scroll.viewport().width() > 0
    finally:
        window.close()
        qapp.processEvents()


def test_main_window_persists_theme_choice(qapp: QApplication, tmp_path: Path, monkeypatch) -> None:
    window = _create_window(tmp_path, qapp, monkeypatch)

    try:
        assert qapp.property("dorkvaultTheme") == "light"
        assert qapp.styleSheet()

        dark_settings = AppSettings(
            theme="dark",
            open_in_browser_behavior="new_window",
            recent_limit=17,
            compact_view_enabled=False,
            last_target="example.com",
        )
        window.settings_service.update(dark_settings)
        window._apply_settings_to_runtime(dark_settings)
        qapp.processEvents()
        assert qapp.property("dorkvaultTheme") == "dark"
        assert qapp.styleSheet()
    finally:
        window.close()
        qapp.processEvents()

    reloaded_settings = SettingsService()
    assert reloaded_settings.settings.theme == "dark"

    reopened = MainWindow(settings_service=reloaded_settings)
    reopened.show()
    qapp.processEvents()
    try:
        assert qapp.property("dorkvaultTheme") == "dark"
        assert reopened.settings_service.settings.theme == "dark"
    finally:
        reopened.close()
        qapp.processEvents()


def test_main_window_uses_valid_saved_geometry_when_it_fits_a_screen(
    qapp: QApplication,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings_service = SettingsService()
    probe_window = MainWindow(settings_service=settings_service)
    available_geometry = probe_window._startup_screen().availableGeometry()
    safe_min_width = probe_window._safe_minimum_width(available_geometry)
    safe_min_height = probe_window._safe_minimum_height(available_geometry)
    probe_window.close()
    target_geometry = {
        "x": available_geometry.left(),
        "y": available_geometry.top() + max(0, available_geometry.height() - safe_min_height),
        "width": safe_min_width,
        "height": safe_min_height,
    }
    settings_service.update(
        AppSettings(
            theme="light",
            open_in_browser_behavior="new_tab",
            recent_limit=25,
            compact_view_enabled=True,
            last_target="example.com",
            window_geometry=target_geometry,
        )
    )

    window = MainWindow(settings_service=settings_service)
    try:
        assert window.geometry() == QRect(
            target_geometry["x"],
            target_geometry["y"],
            target_geometry["width"],
            target_geometry["height"],
        )
    finally:
        window.close()
        qapp.processEvents()


def test_main_window_discards_invalid_saved_geometry_and_centers_fallback(
    qapp: QApplication,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings_service = SettingsService()
    settings_service.update(
        AppSettings(
            theme="light",
            open_in_browser_behavior="new_tab",
            recent_limit=25,
            compact_view_enabled=True,
            last_target="example.com",
            window_geometry={"x": -5000, "y": -4000, "width": 9999, "height": 9999},
        )
    )

    window = MainWindow(settings_service=settings_service)
    try:
        available_geometry = window._startup_screen().availableGeometry()
        fallback_geometry = window._safe_default_geometry(available_geometry)
        assert window.geometry() == fallback_geometry
    finally:
        window.close()
        qapp.processEvents()
