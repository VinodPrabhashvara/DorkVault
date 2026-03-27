"""Application bootstrap for DorkVault."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from dorkvault.core.config import DEFAULT_APP_CONFIG
from dorkvault.core.constants import APP_NAME, ORGANIZATION_NAME
from dorkvault.services.settings_service import SettingsService
from dorkvault.services.theme_manager import ThemeManager
from dorkvault.ui.main_window import MainWindow
from dorkvault.utils.logging_utils import configure_logging
from dorkvault.utils.resource_loader import load_icon, resolve_icon_path
from dorkvault.utils.paths import is_packaged_app


def _describe_window_flags(window: MainWindow) -> list[str]:
    active_flags: list[str] = []
    flag_value = int(window.windowFlags())
    candidates: list[tuple[str, object]] = [
        ("Window", Qt.WindowType.Window),
        ("WindowTitleHint", Qt.WindowType.WindowTitleHint),
        ("WindowSystemMenuHint", Qt.WindowType.WindowSystemMenuHint),
        ("WindowMinimizeButtonHint", Qt.WindowType.WindowMinimizeButtonHint),
        ("WindowMaximizeButtonHint", Qt.WindowType.WindowMaximizeButtonHint),
        ("WindowCloseButtonHint", Qt.WindowType.WindowCloseButtonHint),
        ("FramelessWindowHint", Qt.WindowType.FramelessWindowHint),
        ("CustomizeWindowHint", Qt.WindowType.CustomizeWindowHint),
    ]
    optional_flag_names = ("ExpandedClientAreaHint", "NoTitleBarBackgroundHint")
    for name in optional_flag_names:
        flag = getattr(Qt.WindowType, name, None)
        if flag is not None:
            candidates.append((name, flag))
    for name, flag in candidates:
        if flag_value & int(flag):
            active_flags.append(name)
    return active_flags


def run() -> int:
    """Create and execute the Qt application."""
    logger = configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(DEFAULT_APP_CONFIG.app_name)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setStyle("Fusion")

    icon_path = resolve_icon_path("app_icon.ico", fallback_name="app_icon.svg")
    app_icon = load_icon("app_icon.ico", fallback_name="app_icon.svg")
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    settings_service = SettingsService()
    ThemeManager().apply_theme(app, settings_service.settings.theme)

    try:
        window = MainWindow(settings_service=settings_service)
        if not app_icon.isNull():
            window.setWindowIcon(app_icon)
        active_flags = _describe_window_flags(window)
        print(f"DorkVault pre-show window flags: {hex(int(window.windowFlags()))} {active_flags}")
        logger.info(
            "Resolved startup icon asset.",
            extra={
                "event": "startup_icon_resolved",
                "icon_path": str(icon_path) if icon_path is not None else "",
                "packaged_mode": is_packaged_app(),
                "icon_sizes": [f"{size.width()}x{size.height()}" for size in app_icon.availableSizes()],
                "window_flags_hex": hex(int(window.windowFlags())),
                "window_flags": active_flags,
            },
        )
        window.show()
    except Exception as exc:  # pragma: no cover - UI startup safeguard
        logger.exception(
            "Unable to initialize the main window.",
            extra={
                "event": "application_startup_failed",
                "error": str(exc),
            },
        )
        QMessageBox.critical(
            None,
            APP_NAME,
            "DorkVault could not finish starting. Check the application log for details.",
        )
        return 1

    return app.exec()
