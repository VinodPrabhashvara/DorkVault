"""Application configuration models."""

from __future__ import annotations

from dataclasses import dataclass

from dorkvault.core.constants import APP_NAME


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Static configuration used during application startup."""

    app_name: str = APP_NAME
    # The default size should feel comfortable on a typical desktop display
    # without immediately forcing the user to resize the window.
    window_width: int = 1440
    window_height: int = 900
    # The minimum size is large enough to preserve a usable sidebar, center
    # list, and detail panel, while still allowing the app to fit on smaller
    # laptop displays.
    minimum_width: int = 1140
    minimum_height: int = 720
    sidebar_default_width: int = 220
    list_default_width: int = 680
    detail_default_width: int = 500


DEFAULT_APP_CONFIG = AppConfig()
