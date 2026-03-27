import json

import pytest

from dorkvault.core.exceptions import ExportError
from dorkvault.core.models import Technique
from dorkvault.services.export_service import ExportService


def _sample_technique(*, technique_id: str, name: str, category: str, engine: str) -> Technique:
    return Technique.from_dict(
        {
            "id": technique_id,
            "name": name,
            "category": category,
            "engine": engine,
            "description": f"{name} description",
            "query_template": "site:{domain}",
            "variables": ["domain"],
            "tags": [engine.lower(), "test"],
            "example": "site:example.com",
            "safe_mode": True,
            "reference": f"https://example.com/{technique_id}",
        }
    )


def test_export_service_writes_rendered_query_text(tmp_path) -> None:
    service = ExportService()
    output_path = tmp_path / "query.txt"

    service.export_rendered_query_text(output_path, "site:example.com login")

    assert output_path.read_text(encoding="utf-8") == "site:example.com login\n"


def test_export_service_rejects_empty_rendered_query(tmp_path) -> None:
    service = ExportService()

    with pytest.raises(ValueError, match="Rendered query cannot be empty"):
        service.export_rendered_query_text(tmp_path / "query.txt", "   ")


def test_export_service_writes_techniques_json(tmp_path) -> None:
    service = ExportService()
    output_path = tmp_path / "techniques.json"
    techniques = [
        _sample_technique(
            technique_id="google-one",
            name="Google One",
            category="Google Dorks",
            engine="Google",
        ),
        _sample_technique(
            technique_id="github-one",
            name="GitHub One",
            category="GitHub Search",
            engine="GitHub",
        ),
    ]

    service.export_techniques_json(output_path, techniques, export_name="visible_techniques")

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["export_name"] == "visible_techniques"
    assert payload["count"] == 2
    assert [item["id"] for item in payload["techniques"]] == ["google-one", "github-one"]
    assert payload["techniques"][0]["variables"][0]["name"] == "domain"


def test_export_service_writes_favorites_json(tmp_path) -> None:
    service = ExportService()
    output_path = tmp_path / "favorites.json"
    favorites = [
        _sample_technique(
            technique_id="favorite-one",
            name="Favorite One",
            category="Google Dorks",
            engine="Google",
        )
    ]

    service.export_favorites_json(output_path, favorites)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["export_name"] == "favorites"
    assert payload["count"] == 1
    assert payload["techniques"][0]["id"] == "favorite-one"


def test_export_service_wraps_file_write_failures(tmp_path) -> None:
    service = ExportService()
    missing_parent_path = tmp_path / "missing" / "query.txt"

    with pytest.raises(ExportError, match="could not be exported"):
        service.export_rendered_query_text(missing_parent_path, "site:example.com")
