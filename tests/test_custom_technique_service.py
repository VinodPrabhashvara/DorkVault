import json

import pytest

from dorkvault.core.exceptions import CustomTechniqueError
from dorkvault.services.custom_technique_service import CustomTechniqueService
from dorkvault.services.technique_repository import TechniqueRepository


def test_custom_technique_service_saves_valid_custom_technique(tmp_path) -> None:
    custom_file_path = tmp_path / "techniques" / "custom_queries.json"
    service = CustomTechniqueService(custom_file_path=custom_file_path)

    technique = service.create_custom_technique(
        {
            "name": "Custom GitHub Workflow Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Look for workflow files mentioning a keyword.",
            "query_template": "path:.github/workflows {keyword}",
            "variables": "keyword",
            "tags": "github, workflows, ci",
            "example": "path:.github/workflows payments",
        }
    )

    assert technique.id == "github-search-custom-github-workflow-search"
    assert technique.category == "GitHub Search"
    assert technique.variable_names == ["keyword"]

    payload = json.loads(custom_file_path.read_text(encoding="utf-8"))
    assert payload["category_id"] == "custom_queries"
    assert len(payload["techniques"]) == 1
    assert payload["techniques"][0]["name"] == "Custom GitHub Workflow Search"


def test_custom_technique_service_validates_against_schema(tmp_path) -> None:
    custom_file_path = tmp_path / "techniques" / "custom_queries.json"
    service = CustomTechniqueService(custom_file_path=custom_file_path)

    with pytest.raises(ValueError, match="references undefined variables"):
        service.create_custom_technique(
            {
                "name": "Broken Custom Query",
                "category": "Google Dorks",
                "engine": "Google",
                "description": "Invalid placeholder declaration.",
                "query_template": "site:{domain} \"{company}\"",
                "variables": "domain",
                "tags": "google, test",
                "example": "site:example.com \"Example Corp\"",
            }
        )


def test_custom_technique_service_updates_only_existing_custom_techniques(tmp_path) -> None:
    custom_file_path = tmp_path / "techniques" / "custom_queries.json"
    service = CustomTechniqueService(custom_file_path=custom_file_path)
    created = service.create_custom_technique(
        {
            "name": "Custom GitHub Workflow Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Look for workflow files mentioning a keyword.",
            "query_template": "path:.github/workflows {keyword}",
            "variables": "keyword",
            "tags": "github, workflows, ci",
            "example": "path:.github/workflows payments",
        }
    )

    updated = service.update_custom_technique(
        created.id,
        {
            "name": "Updated GitHub Workflow Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Updated description.",
            "query_template": "path:.github/workflows {keyword} language:yaml",
            "variables": "keyword",
            "tags": "github, workflows, yaml",
            "example": "path:.github/workflows payments language:yaml",
        },
    )

    assert updated.id == created.id
    assert updated.name == "Updated GitHub Workflow Search"
    payload = json.loads(custom_file_path.read_text(encoding="utf-8"))
    assert payload["techniques"][0]["name"] == "Updated GitHub Workflow Search"

    with pytest.raises(ValueError, match="Only user-created custom techniques can be edited"):
        service.update_custom_technique("missing-technique", {"name": "Nope"})


def test_custom_technique_service_deletes_custom_techniques(tmp_path) -> None:
    custom_file_path = tmp_path / "techniques" / "custom_queries.json"
    service = CustomTechniqueService(custom_file_path=custom_file_path)
    created = service.create_custom_technique(
        {
            "name": "Custom GitHub Workflow Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Look for workflow files mentioning a keyword.",
            "query_template": "path:.github/workflows {keyword}",
            "variables": "keyword",
            "tags": "github, workflows, ci",
            "example": "path:.github/workflows payments",
        }
    )

    assert service.is_custom_technique(created) is True
    service.delete_custom_technique(created.id)

    payload = json.loads(custom_file_path.read_text(encoding="utf-8"))
    assert payload["techniques"] == []
    assert service.is_custom_technique(created.id) is False

    with pytest.raises(ValueError, match="Only user-created custom techniques can be deleted"):
        service.delete_custom_technique(created.id)


def test_repository_merges_built_in_and_custom_techniques(tmp_path) -> None:
    built_in_dir = tmp_path / "built_in"
    built_in_dir.mkdir(parents=True)
    (built_in_dir / "google_dorks.json").write_text(
        json.dumps(
            {
                "category_id": "google_dorks",
                "category_name": "Google Dorks",
                "description": "Built-in Google queries",
                "display_order": 10,
                "techniques": [
                    {
                        "id": "google-built-in",
                        "name": "Google Built In",
                        "category": "Google Dorks",
                        "engine": "Google",
                        "description": "Built-in technique.",
                        "query_template": "site:{domain}",
                        "variables": ["domain"],
                        "tags": ["google"],
                        "example": "site:example.com",
                        "safe_mode": True,
                        "reference": "https://example.com/google-built-in",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    custom_service = CustomTechniqueService(custom_file_path=tmp_path / "user" / "custom_queries.json")
    custom_service.create_custom_technique(
        {
            "name": "Custom Certificate Search",
            "category": "CT Logs",
            "engine": "Censys",
            "description": "Search custom certificate data.",
            "query_template": "parsed.names: {domain}",
            "variables": "domain",
            "tags": "ct, certs",
            "example": "parsed.names: example.com",
        }
    )

    repository = TechniqueRepository(data_dir=built_in_dir, custom_data_dir=custom_service.custom_file_path.parent)
    categories = repository.load()

    assert len(repository.all_techniques()) == 2
    assert any(technique.id == "ct-logs-custom-certificate-search" for technique in repository.all_techniques())
    assert any(category.name == "CT Logs" for category in categories)


def test_custom_technique_service_raises_custom_technique_error_for_invalid_json_file(tmp_path) -> None:
    custom_file_path = tmp_path / "techniques" / "custom_queries.json"
    custom_file_path.parent.mkdir(parents=True, exist_ok=True)
    custom_file_path.write_text("{ invalid json", encoding="utf-8")
    service = CustomTechniqueService(custom_file_path=custom_file_path)

    with pytest.raises(CustomTechniqueError, match="custom technique file is invalid"):
        service.is_custom_technique("anything")
