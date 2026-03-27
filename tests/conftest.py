from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
from typing import Any

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dorkvault.core.models import Technique
from dorkvault.utils.paths import get_data_dir


@pytest.fixture
def bundled_techniques_dir() -> Path:
    """Return the bundled technique catalog directory used by the app."""
    return get_data_dir() / "techniques"


@pytest.fixture
def make_technique_payload() -> Callable[..., dict[str, Any]]:
    """Build realistic technique payloads with small test-specific overrides."""

    def _make_technique_payload(**overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": "sample-technique",
            "name": "Sample Technique",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Search for indexed content related to a target domain.",
            "query_template": "site:{domain} {keyword}",
            "variables": [
                {
                    "name": "domain",
                    "description": "Target domain name.",
                    "required": True,
                    "example": "example.com",
                },
                {
                    "name": "keyword",
                    "description": "Query keyword.",
                    "required": True,
                    "example": "login",
                },
            ],
            "tags": ["google", "search", "test"],
            "example": "site:example.com login",
            "safe_mode": True,
            "reference": "https://example.com/reference",
            "launch_url": "https://www.google.com/search?q={query}",
        }
        payload.update(overrides)
        return payload

    return _make_technique_payload


@pytest.fixture
def make_technique(make_technique_payload: Callable[..., dict[str, Any]]) -> Callable[..., Technique]:
    """Create validated Technique instances from shared payload defaults."""

    def _make_technique(**overrides: Any) -> Technique:
        return Technique.from_dict(make_technique_payload(**overrides))

    return _make_technique


@pytest.fixture
def qapp():
    """Provide a shared QApplication for widget-level tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
