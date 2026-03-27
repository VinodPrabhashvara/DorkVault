from dorkvault.core.models import Technique
from dorkvault.services.launcher_service import LauncherService


class _FakeBrowserService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def open_technique(
        self,
        technique: Technique,
        rendered_query: str,
        *,
        variable_values: dict[str, str] | None = None,
        behavior: str = "new_tab",
    ) -> str:
        self.calls.append(
            {
                "technique_id": technique.id,
                "rendered_query": rendered_query,
                "variable_values": variable_values,
                "behavior": behavior,
            }
        )
        return "https://example.test/search?q=ok"


def test_launcher_service_uses_normalized_domain_for_launches() -> None:
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
    browser_service = _FakeBrowserService()
    launcher = LauncherService(browser_service=browser_service)

    url = launcher.launch(
        technique,
        "https://www.example.com/login",
        open_behavior="new_window",
    )

    assert url == "https://example.test/search?q=ok"
    assert browser_service.calls == [
        {
            "technique_id": "google-domain-search",
            "rendered_query": "site:www.example.com login",
            "variable_values": {"domain": "www.example.com"},
            "behavior": "new_window",
        }
    ]
