from dorkvault.core.models import Technique
from dorkvault.services.clipboard_service import TechniqueClipboardService


def test_clipboard_service_copies_rendered_query_when_available() -> None:
    technique = Technique.from_dict(
        {
            "id": "google-domain-search",
            "name": "Google Domain Search",
            "category": "Google Dorks",
            "engine": "Google",
            "description": "Search a domain.",
            "query_template": "site:{domain} login",
            "variables": ["domain"],
            "tags": ["google"],
            "example": "site:example.com login",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )

    result = TechniqueClipboardService().build_copy_result(technique, "example.com")

    assert result.text == "site:example.com login"
    assert result.feedback_message == "Rendered query copied to clipboard."
    assert result.source == "rendered_query"


def test_clipboard_service_falls_back_to_template_when_render_is_unavailable() -> None:
    technique = Technique.from_dict(
        {
            "id": "multi-variable-search",
            "name": "Multi Variable Search",
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

    result = TechniqueClipboardService().build_copy_result(technique, "example")

    assert result.text == "\"{company}\" site:{domain}"
    assert result.feedback_message == "Query template copied to clipboard."
    assert result.source == "template"
