import pytest

from dorkvault.core.exceptions import BrowserIntegrationError, UnsupportedBrowserEngineError
from dorkvault.core.models import Technique
from dorkvault.services.browser_service import BrowserService


def _technique(engine: str, *, launch_url: str = "") -> Technique:
    return Technique.from_dict(
        {
            "id": f"{engine.lower().replace(' ', '-')}-technique",
            "name": f"{engine} Technique",
            "category": "Search",
            "engine": engine,
            "description": "Test technique",
            "query_template": "\"{keyword}\"",
            "variables": ["keyword"],
            "tags": ["test"],
            "example": "\"example\"",
            "safe_mode": True,
            "reference": "https://example.com/reference",
            "launch_url": launch_url,
        }
    )


def test_browser_service_builds_google_url() -> None:
    url = BrowserService().build_url(_technique("Google"), "\"Example Corp\" login")
    assert url == "https://www.google.com/search?q=%22Example+Corp%22+login"


def test_browser_service_builds_github_url() -> None:
    url = BrowserService().build_url(_technique("GitHub"), "\"Example Corp\" secret")
    assert url == "https://github.com/search?q=%22Example+Corp%22+secret&type=code"


def test_browser_service_builds_wayback_url() -> None:
    url = BrowserService().build_url(_technique("Wayback Machine"), "example.com")
    assert url == "https://web.archive.org/web/*/example.com"


def test_browser_service_builds_shodan_url() -> None:
    url = BrowserService().build_url(_technique("Shodan"), "hostname:example.com")
    assert url == "https://www.shodan.io/search?query=hostname%3Aexample.com"


def test_browser_service_builds_censys_url() -> None:
    url = BrowserService().build_url(_technique("Censys"), "services.http.response.html_title: Example Corp")
    assert (
        url
        == "https://search.censys.io/search?resource=hosts&q=services.http.response.html_title%3A+Example+Corp"
    )


def test_browser_service_formats_technique_launch_url_with_variables() -> None:
    technique = _technique(
        "Google",
        launch_url="https://www.google.com/search?q={query}&source={keyword}",
    )

    url = BrowserService().build_url(
        technique,
        "\"Example Corp\" login",
        variable_values={"keyword": "Example Corp"},
    )

    assert (
        url
        == "https://www.google.com/search?q=%22Example+Corp%22+login&source=Example+Corp"
    )


def test_browser_service_raises_for_unsupported_engine() -> None:
    with pytest.raises(UnsupportedBrowserEngineError, match="Unsupported browser engine"):
        BrowserService().build_url(_technique("UnknownEngine"), "test")


def test_browser_service_raises_for_invalid_launch_url_template() -> None:
    technique = _technique("Google", launch_url="https://example.com/search?q={missing_value}")

    with pytest.raises(BrowserIntegrationError, match="launch URL is invalid"):
        BrowserService().build_url(technique, "\"Example Corp\"")


def test_browser_service_raises_when_browser_cannot_be_opened(monkeypatch) -> None:
    service = BrowserService()

    monkeypatch.setattr("webbrowser.open_new_tab", lambda _url: False)

    with pytest.raises(BrowserIntegrationError, match="could not be opened"):
        service.open_url("https://example.com", behavior="new_tab")
