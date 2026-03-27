from dorkvault.core.models import Technique
from dorkvault.services.technique_preview_service import TechniquePreviewService


def test_preview_service_renders_query_with_target_input() -> None:
    technique = Technique.from_dict(
        {
            "id": "google-domain-search",
            "name": "Google Domain Search",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Search indexed content for a domain.",
            "query_template": "site:{domain} login",
            "variables": ["domain"],
            "tags": ["google"],
            "example": "site:example.com login",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    preview_state = TechniquePreviewService().build_preview(technique, "example.com")

    assert preview_state.preview_query == "site:example.com login"
    assert "Rendered using domain" in preview_state.status_text
    assert preview_state.render_error == ""


def test_preview_service_shows_normalized_domain_helper_note() -> None:
    technique = Technique.from_dict(
        {
            "id": "google-domain-search",
            "name": "Google Domain Search",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Search indexed content for a domain.",
            "query_template": "site:{domain} login",
            "variables": ["domain"],
            "tags": ["google"],
            "example": "site:example.com login",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    preview_state = TechniquePreviewService().build_preview(
        technique,
        "https://www.example.com/login",
    )

    assert preview_state.preview_query == "site:www.example.com login"
    assert "Rendered using domain: www.example.com" in preview_state.status_text
    assert "Using normalized domain: www.example.com" in preview_state.status_text
    assert preview_state.render_error == ""


def test_preview_service_uses_example_when_target_is_missing() -> None:
    technique = Technique.from_dict(
        {
            "id": "github-company-search",
            "name": "GitHub Company Search",
            "category": "GitHub Search",
            "engine": "GitHub",
            "description": "Search company references in public code.",
            "query_template": "\"{company}\" token",
            "variables": ["company"],
            "tags": ["github"],
            "example": "\"Example Corp\" token",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    preview_state = TechniquePreviewService().build_preview(technique, "")

    assert preview_state.preview_query == "\"Example Corp\" token"
    assert "Enter company above" in preview_state.status_text


def test_preview_service_reports_multi_variable_requirement() -> None:
    technique = Technique.from_dict(
        {
            "id": "multi-variable-technique",
            "name": "Multi Variable Technique",
            "category": "Custom",
            "engine": "Custom",
            "description": "Requires more than one variable.",
            "query_template": "\"{company}\" site:{domain}",
            "variables": ["company", "domain"],
            "tags": ["custom"],
            "example": "\"Example Corp\" site:example.com",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    preview_state = TechniquePreviewService().build_preview(technique, "example")

    assert preview_state.preview_query == "\"Example Corp\" site:example.com"
    assert "Cannot render from one target input" in preview_state.status_text
    assert preview_state.render_error == "multiple_variables_required"
