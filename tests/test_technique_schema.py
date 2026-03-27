import pytest

from dorkvault.core.models import Technique, TechniqueVariable


def test_technique_schema_accepts_valid_record() -> None:
    technique = Technique.from_dict(
        {
            "id": "github-org-secrets",
            "name": "GitHub Org Secrets Hunt",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Search public code for references to a target organization and secret keywords.",
            "query_template": "\"{target}\" (token OR secret OR password)",
            "variables": [
                {
                    "name": "target",
                    "description": "Organization or company name.",
                    "required": True,
                    "example": "example-corp"
                }
            ],
            "tags": ["github", "secrets", "osint"],
            "example": "\"example-corp\" (token OR secret OR password)",
            "safe_mode": True,
            "reference": "https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax",
            "launch_url": "https://github.com/search?q={query}&type=code"
        }
    )

    assert technique.id == "github-org-secrets"
    assert technique.engine == "GitHub"
    assert technique.variable_names == ["target"]
    assert technique.render_query({"target": "example-corp"}) == "\"example-corp\" (token OR secret OR password)"


def test_technique_schema_normalizes_legacy_target_record() -> None:
    technique = Technique.from_dict(
        {
            "id": "legacy-google-dork",
            "name": "Legacy Google Dork",
            "provider": "Google",
            "description": "Legacy starter record.",
            "query_template": "site:{target} ext:sql",
            "target_hint": "example.com",
            "tags": ["google", "legacy"],
            "launch_url": "https://www.google.com/search?q={query}",
            "notes": "Legacy note"
        },
        default_category="Google Dorks",
    )

    assert technique.category == "Google Dorks"
    assert technique.engine == "Google"
    assert technique.variable_names == ["target"]
    assert technique.example == "site:example.com ext:sql"
    assert technique.reference == "https://www.google.com/search?q={query}"


def test_technique_schema_rejects_missing_required_field() -> None:
    with pytest.raises(ValueError, match="name"):
        Technique.from_dict(
            {
                "id": "missing-name",
                "category": "GitHub Search",
                "engine": "GitHub",
                "description": "Invalid record.",
                "query_template": "\"{target}\"",
                "variables": ["target"],
                "tags": ["invalid"],
                "example": "\"example\"",
                "safe_mode": True,
                "reference": "https://example.com/reference"
            }
        )


def test_technique_schema_rejects_undefined_template_variable() -> None:
    with pytest.raises(ValueError, match="undefined variables"):
        Technique.from_dict(
            {
                "id": "bad-variable-map",
                "name": "Bad Variable Map",
                "category": "Search",
                "engine": "Generic",
                "description": "References an undeclared placeholder.",
                "query_template": "\"{company}\" filetype:pdf",
                "variables": ["target"],
                "tags": ["invalid"],
                "example": "\"example corp\" filetype:pdf",
                "safe_mode": True,
                "reference": "https://example.com/reference"
            }
        )


def test_technique_schema_rejects_duplicate_variables() -> None:
    with pytest.raises(ValueError, match="Duplicate technique variable"):
        Technique(
            id="duplicate-vars",
            name="Duplicate Variables",
            category="Generic",
            engine="Generic",
            description="Invalid variable duplication.",
            query_template="{target}",
            variables=[
                TechniqueVariable(name="target"),
                TechniqueVariable(name="target"),
            ],
            tags=["invalid"],
            example="example.com",
            safe_mode=True,
            reference="https://example.com/reference",
        )


def test_technique_variable_rejects_invalid_name() -> None:
    with pytest.raises(ValueError, match="letters, numbers, or underscores"):
        TechniqueVariable(name="bad-name")


def test_technique_schema_picks_single_target_primary_variable() -> None:
    technique = Technique.from_dict(
        {
            "id": "google-domain-only",
            "name": "Google Domain Only",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Render from a single domain input.",
            "query_template": "site:{domain}",
            "variables": [{"name": "domain", "required": True}],
            "tags": ["google", "domain"],
            "example": "site:example.com",
            "safe_mode": True,
            "reference": "https://example.com/google-domain-only",
        }
    )

    assert technique.primary_variable_name == "domain"
    assert technique.build_variables_from_target_input(" example.com ") == {"domain": "example.com"}


def test_technique_schema_normalizes_url_input_for_domain_variables() -> None:
    technique = Technique.from_dict(
        {
            "id": "google-domain-only",
            "name": "Google Domain Only",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Render from a single domain input.",
            "query_template": "site:{domain}",
            "variables": [{"name": "domain", "required": True}],
            "tags": ["google", "domain"],
            "example": "site:example.com",
            "safe_mode": True,
            "reference": "https://example.com/google-domain-only",
        }
    )

    assert technique.build_variables_from_target_input(
        "https://www.example.com/login",
    ) == {"domain": "www.example.com"}
    assert technique.build_query("http://api.example.com/v1/users") == "site:api.example.com"


def test_technique_schema_search_text_includes_tags_engine_and_variables() -> None:
    technique = Technique.from_dict(
        {
            "id": "github-workflow-search",
            "name": "Workflow Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Find workflow files with target keywords.",
            "query_template": "path:.github/workflows {keyword}",
            "variables": [{"name": "keyword", "required": True}],
            "tags": ["github", "workflow", "ci"],
            "example": "path:.github/workflows payments",
            "safe_mode": True,
            "reference": "https://example.com/workflow-search",
        }
    )

    searchable_text = technique.search_text()

    assert "github search" in searchable_text
    assert "github" in searchable_text
    assert "workflow" in searchable_text
    assert "keyword" in searchable_text
