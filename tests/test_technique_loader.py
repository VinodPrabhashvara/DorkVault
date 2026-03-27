import json
import logging

import pytest

from dorkvault.core.exceptions import DataValidationError, TechniqueLoadError
from dorkvault.services.technique_loader import TechniqueLoader, TechniqueLoaderConfig


def _write_category_file(tmp_path, file_name: str, category_name: str, techniques: list[dict]) -> None:
    payload = {
        "category_id": file_name.removesuffix(".json"),
        "category_name": category_name,
        "description": f"{category_name} techniques",
        "display_order": 10,
        "techniques": techniques,
    }
    target_path = tmp_path / file_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _technique_record(
    *,
    technique_id: str,
    name: str,
    category: str,
    engine: str,
    query_template: str = "\"{target}\"",
) -> dict:
    return {
        "id": technique_id,
        "name": name,
        "category": category,
        "engine": engine,
        "description": f"{name} description",
        "query_template": query_template,
        "variables": ["target"],
        "tags": [engine.lower(), "test"],
        "example": query_template.format(target="example"),
        "safe_mode": True,
        "reference": f"https://example.com/{technique_id}",
        "launch_url": "https://example.com/search?q={query}",
    }


def test_loader_merges_multiple_json_files(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "google_dorks.json",
        "Google Dorks",
        [_technique_record(technique_id="google-1", name="Google One", category="Google Dorks", engine="Google")],
    )
    _write_category_file(
        tmp_path,
        "github_queries.json",
        "GitHub Queries",
        [_technique_record(technique_id="github-1", name="GitHub One", category="GitHub Queries", engine="GitHub")],
    )
    _write_category_file(
        tmp_path,
        "shodan_queries.json",
        "Shodan Queries",
        [_technique_record(technique_id="shodan-1", name="Shodan One", category="Shodan Queries", engine="Shodan")],
    )

    loader = TechniqueLoader(tmp_path)
    result = loader.load()

    assert result.loaded_files == ["github_queries.json", "google_dorks.json", "shodan_queries.json"]
    assert [category.name for category in result.categories] == [
        "GitHub Queries",
        "Google Dorks",
        "Shodan Queries",
    ]
    assert [technique.id for technique in result.techniques] == ["github-1", "google-1", "shodan-1"]
    assert result.skipped_entries == 0


def test_loader_raises_for_invalid_entry_in_strict_mode(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "custom_queries.json",
        "Custom Queries",
        [
            _technique_record(
                technique_id="custom-valid",
                name="Custom Valid",
                category="Custom Queries",
                engine="Custom",
            ),
            {
                "id": "custom-invalid",
                "category": "Custom Queries",
                "engine": "Custom",
                "description": "Missing required name field",
                "query_template": "\"{target}\"",
                "variables": ["target"],
                "tags": ["custom"],
                "example": "\"example\"",
                "safe_mode": True,
                "reference": "https://example.com/custom-invalid",
            },
        ],
    )

    loader = TechniqueLoader(tmp_path)

    with pytest.raises(DataValidationError, match="custom_queries.json entry #2"):
        loader.load()


def test_loader_skips_invalid_entry_when_configured(tmp_path, caplog) -> None:
    _write_category_file(
        tmp_path,
        "cloud_queries.json",
        "Cloud Queries",
        [
            _technique_record(
                technique_id="cloud-valid",
                name="Cloud Valid",
                category="Cloud Queries",
                engine="Google",
            ),
            {
                "id": "cloud-invalid",
                "name": "Cloud Invalid",
                "category": "Cloud Queries",
                "engine": "Google",
                "description": "Has undeclared variable",
                "query_template": "\"{company}\" site:storage.googleapis.com",
                "variables": ["target"],
                "tags": ["cloud"],
                "example": "\"example\" site:storage.googleapis.com",
                "safe_mode": True,
                "reference": "https://example.com/cloud-invalid",
            },
        ],
    )

    caplog.set_level(logging.WARNING)
    loader = TechniqueLoader(
        tmp_path,
        config=TechniqueLoaderConfig(skip_invalid_entries=True),
    )
    result = loader.load()

    assert len(result.techniques) == 1
    assert result.techniques[0].id == "cloud-valid"
    assert result.skipped_entries == 1
    assert "Skipping invalid technique entry" in caplog.text
    assert "cloud_queries.json entry #2" in caplog.text


def test_loader_raises_for_duplicate_technique_ids(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "google_dorks.json",
        "Google Dorks",
        [_technique_record(technique_id="duplicate-id", name="Google Duplicate", category="Google Dorks", engine="Google")],
    )
    _write_category_file(
        tmp_path,
        "custom_queries.json",
        "Custom Queries",
        [_technique_record(technique_id="duplicate-id", name="Custom Duplicate", category="Custom Queries", engine="Custom")],
    )

    loader = TechniqueLoader(tmp_path)

    with pytest.raises(DataValidationError, match="duplicate technique id 'duplicate-id'"):
        loader.load()


def test_loader_raises_for_invalid_json(tmp_path) -> None:
    (tmp_path / "wayback_queries.json").write_text("{ bad json", encoding="utf-8")

    loader = TechniqueLoader(tmp_path)

    with pytest.raises(TechniqueLoadError, match="Invalid JSON in wayback_queries.json"):
        loader.load()


def test_loader_discovers_recursive_pack_directories_and_group_metadata(tmp_path) -> None:
    payload = {
        "category_id": "google_dorks",
        "category_name": "Google Dorks",
        "description": "Google techniques",
        "display_order": 10,
        "category_group_id": "search_engines",
        "category_group_name": "Search Engines",
        "category_group_display_order": 20,
        "techniques": [
            _technique_record(
                technique_id="google-login",
                name="Google Login",
                category="Google Dorks",
                engine="Google",
            )
        ],
    }
    nested_path = tmp_path / "web" / "search" / "google_dorks.json"
    nested_path.parent.mkdir(parents=True, exist_ok=True)
    nested_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    loader = TechniqueLoader(tmp_path)
    result = loader.load()

    assert result.loaded_files == ["web/search/google_dorks.json"]
    assert len(result.categories) == 1
    category = result.categories[0]
    assert category.group_id == "search_engines"
    assert category.group_name == "Search Engines"
    assert category.group_display_order == 20
    assert category.techniques[0].source_file == "web/search/google_dorks.json"
