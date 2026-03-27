import pytest

from dorkvault.core.exceptions import MalformedTemplateError, MissingVariableError
from dorkvault.core.models import Technique
from dorkvault.services.query_renderer import QueryRenderer


def _sample_technique() -> Technique:
    return Technique.from_dict(
        {
            "id": "google-domain-search",
            "name": "Google Domain Search",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Search for indexed content on a domain with a keyword.",
            "query_template": "site:{domain} {keyword}",
            "variables": [
                {
                    "name": "domain",
                    "description": "Target domain.",
                    "required": True,
                    "example": "example.com",
                },
                {
                    "name": "keyword",
                    "description": "Search keyword.",
                    "required": True,
                    "example": "login",
                },
            ],
            "tags": ["google", "search"],
            "example": "site:example.com login",
            "safe_mode": True,
            "reference": "https://support.google.com/websearch/answer/2466433",
            "launch_url": "https://www.google.com/search?q={query}",
        }
    )


def test_query_renderer_renders_normal_case() -> None:
    renderer = QueryRenderer()
    technique = _sample_technique()

    result = renderer.render(
        technique,
        {
            "domain": "example.com",
            "keyword": "login",
        },
    )

    assert result.query == "site:example.com login"
    assert result.variables == {"domain": "example.com", "keyword": "login"}


def test_query_renderer_uses_variable_defaults() -> None:
    renderer = QueryRenderer()
    technique = Technique.from_dict(
        {
            "id": "keyword-default-search",
            "name": "Keyword Default Search",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Uses a default keyword when one is not supplied.",
            "query_template": "site:{domain} {keyword}",
            "variables": [
                {"name": "domain", "required": True, "example": "example.com"},
                {"name": "keyword", "required": False, "default": "admin"},
            ],
            "tags": ["google"],
            "example": "site:example.com admin",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    result = renderer.render(technique, {"domain": "example.com"})

    assert result.query == "site:example.com admin"


def test_query_renderer_raises_for_missing_required_variables() -> None:
    renderer = QueryRenderer()
    technique = _sample_technique()

    with pytest.raises(MissingVariableError, match="requires variable 'keyword'"):
        renderer.render(
            technique,
            {
                "domain": "example.com",
            },
        )


def test_query_renderer_raises_for_malformed_templates() -> None:
    renderer = QueryRenderer()

    with pytest.raises(MalformedTemplateError, match="Malformed query template"):
        renderer.template_variables("site:{domain")


def test_query_renderer_supports_engine_hooks() -> None:
    renderer = QueryRenderer()
    technique = _sample_technique()

    renderer.register_engine_hook("google", lambda _technique, query, _values: query.upper())
    result = renderer.render(
        technique,
        {
            "domain": "example.com",
            "keyword": "login",
        },
    )

    assert result.query == "SITE:EXAMPLE.COM LOGIN"


def test_query_renderer_normalizes_whitespace_in_variable_values() -> None:
    renderer = QueryRenderer()
    technique = _sample_technique()

    result = renderer.render(
        technique,
        {
            " domain ": " example.com ",
            "keyword": " login ",
        },
    )

    assert result.query == "site:example.com login"
    assert result.variables == {"domain": "example.com", "keyword": "login"}
