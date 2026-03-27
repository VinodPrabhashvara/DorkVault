"""Browser URL building and launch helpers for search-engine techniques."""

from __future__ import annotations

import logging
import webbrowser
from typing import Mapping
from urllib.parse import quote, quote_plus

from dorkvault.core.constants import APP_NAME
from dorkvault.core.exceptions import BrowserIntegrationError, UnsupportedBrowserEngineError
from dorkvault.core.models import Technique


class BrowserService:
    """Build and open search URLs for supported technique engines."""

    _ENGINE_ALIASES = {
        "google": "google",
        "github": "github",
        "wayback": "wayback",
        "wayback machine": "wayback",
        "internet archive": "wayback",
        "shodan": "shodan",
        "censys": "censys",
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(APP_NAME)

    def build_url(
        self,
        technique: Technique,
        rendered_query: str,
        *,
        variable_values: Mapping[str, str] | None = None,
    ) -> str:
        """Build a launchable browser URL for a rendered query."""
        cleaned_query = rendered_query.strip()
        if not cleaned_query:
            raise ValueError("Rendered query cannot be empty.")

        normalized_values = self._normalize_values(variable_values or {})
        if technique.launch_url:
            return self._format_launch_url(
                technique.launch_url,
                rendered_query=cleaned_query,
                variable_values=normalized_values,
            )

        normalized_engine = self._normalize_engine_name(technique.engine)
        if normalized_engine == "google":
            return f"https://www.google.com/search?q={quote_plus(cleaned_query)}"
        if normalized_engine == "github":
            return f"https://github.com/search?q={quote_plus(cleaned_query)}&type=code"
        if normalized_engine == "wayback":
            return f"https://web.archive.org/web/*/{quote(cleaned_query, safe='')}"
        if normalized_engine == "shodan":
            return f"https://www.shodan.io/search?query={quote_plus(cleaned_query)}"
        if normalized_engine == "censys":
            return f"https://search.censys.io/search?resource=hosts&q={quote_plus(cleaned_query)}"

        raise UnsupportedBrowserEngineError(
            f"Unsupported browser engine '{technique.engine}' for technique '{technique.id}'."
        )

    def open_url(self, url: str, *, behavior: str = "new_tab") -> str:
        """Open a URL in the default browser."""
        normalized_behavior = behavior.strip().lower()
        try:
            if normalized_behavior == "same_window":
                opened = webbrowser.open(url, new=0)
            elif normalized_behavior == "new_window":
                opened = webbrowser.open_new(url)
            else:
                opened = webbrowser.open_new_tab(url)
        except webbrowser.Error as exc:
            self.logger.exception(
                "Browser launch raised an error.",
                extra={
                    "event": "browser_open_failed",
                    "url": url,
                    "behavior": normalized_behavior,
                    "error": str(exc),
                },
            )
            raise BrowserIntegrationError("The default browser could not be opened.") from exc

        if not opened:
            self.logger.warning(
                "Browser launch returned a failure result.",
                extra={
                    "event": "browser_open_returned_false",
                    "url": url,
                    "behavior": normalized_behavior,
                },
            )
            raise BrowserIntegrationError("The default browser could not be opened.")

        self.logger.info(
            "Opened URL in the default browser.",
            extra={
                "event": "browser_opened",
                "url": url,
                "behavior": normalized_behavior,
            },
        )
        return url

    def open_technique(
        self,
        technique: Technique,
        rendered_query: str,
        *,
        variable_values: Mapping[str, str] | None = None,
        behavior: str = "new_tab",
    ) -> str:
        """Build and open the browser URL for a technique."""
        url = self.build_url(technique, rendered_query, variable_values=variable_values)
        return self.open_url(url, behavior=behavior)

    def _format_launch_url(
        self,
        launch_url: str,
        *,
        rendered_query: str,
        variable_values: Mapping[str, str],
    ) -> str:
        primary_value = next(iter(variable_values.values()), "")
        format_values: dict[str, str] = {
            "query": quote_plus(rendered_query),
            "raw_query": rendered_query,
            "target": quote_plus(primary_value),
            "raw_target": primary_value,
        }

        for name, raw_value in variable_values.items():
            format_values[name] = quote_plus(raw_value)
            format_values[f"raw_{name}"] = raw_value

        try:
            return launch_url.format(**format_values)
        except (KeyError, ValueError) as exc:
            raise BrowserIntegrationError("Technique launch URL is invalid.") from exc

    def _normalize_engine_name(self, engine_name: str) -> str:
        normalized_name = engine_name.strip().lower()
        if not normalized_name:
            raise UnsupportedBrowserEngineError("Technique engine is empty.")
        return self._ENGINE_ALIASES.get(normalized_name, normalized_name)

    @staticmethod
    def _normalize_values(variable_values: Mapping[str, str]) -> dict[str, str]:
        return {
            str(key).strip(): str(value).strip()
            for key, value in variable_values.items()
            if str(key).strip()
        }
