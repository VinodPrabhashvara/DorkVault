"""Technique launch behavior."""

from __future__ import annotations

from dorkvault.core.models import Technique
from dorkvault.services.browser_service import BrowserService


class LauncherService:
    """Open rendered technique URLs in the user's default browser."""

    def __init__(self, browser_service: BrowserService | None = None) -> None:
        self.browser_service = browser_service or BrowserService()

    def launch(self, technique: Technique, target: str, *, open_behavior: str = "new_tab") -> str:
        cleaned_target = target.strip()
        if not cleaned_target:
            raise ValueError("A target is required before launching a technique.")

        variable_values = technique.build_variables_from_target_input(cleaned_target)
        rendered_query = technique.render_query(variable_values)
        return self.browser_service.open_technique(
            technique,
            rendered_query,
            variable_values=variable_values,
            behavior=open_behavior,
        )
