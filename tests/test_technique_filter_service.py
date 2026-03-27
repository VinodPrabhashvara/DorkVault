from dorkvault.core.models import Technique
from dorkvault.services.technique_filter_service import TechniqueFilterCriteria, TechniqueFilterService


def _technique(
    *,
    technique_id: str,
    name: str,
    category: str,
    description: str,
    tags: list[str],
    engine: str = "Google",
) -> Technique:
    return Technique.from_dict(
        {
            "id": technique_id,
            "name": name,
            "category": category,
            "engine": engine,
            "description": description,
            "query_template": "\"{keyword}\"",
            "variables": ["keyword"],
            "tags": tags,
            "example": "\"example\"",
            "safe_mode": True,
            "reference": "https://example.com/reference",
        }
    )


def test_filter_service_matches_name_description_category_and_tags() -> None:
    service = TechniqueFilterService()
    techniques = [
        _technique(
            technique_id="google-admin",
            name="Admin Portal Search",
            category="Google Dorks",
            description="Find indexed admin pages for a target.",
            tags=["google", "admin", "login"],
        ),
        _technique(
            technique_id="ct-certs",
            name="Certificate Search",
            category="CT Logs",
            description="Review historical certificate records.",
            tags=["crt-sh", "certificates"],
            engine="crt.sh",
        ),
    ]

    assert [item.id for item in service.filter(techniques, TechniqueFilterCriteria(search_text="admin"))] == [
        "google-admin"
    ]
    assert [item.id for item in service.filter(techniques, TechniqueFilterCriteria(search_text="historical"))] == [
        "ct-certs"
    ]
    assert [item.id for item in service.filter(techniques, TechniqueFilterCriteria(search_text="ct logs"))] == [
        "ct-certs"
    ]
    assert [item.id for item in service.filter(techniques, TechniqueFilterCriteria(search_text="certificates"))] == [
        "ct-certs"
    ]


def test_filter_service_combines_category_and_search_text() -> None:
    service = TechniqueFilterService()
    techniques = [
        _technique(
            technique_id="google-docs",
            name="Public Document Search",
            category="Google Dorks",
            description="Search for indexed documents on a domain.",
            tags=["google", "documents"],
        ),
        _technique(
            technique_id="github-docs",
            name="Workflow Reference Search",
            category="GitHub Search",
            description="Find public workflow references for a company.",
            tags=["github", "workflow"],
            engine="GitHub",
        ),
    ]

    filtered = service.filter(
        techniques,
        TechniqueFilterCriteria(category_name="GitHub Search", search_text="workflow"),
    )

    assert [item.id for item in filtered] == ["github-docs"]


def test_filter_service_returns_all_for_empty_criteria() -> None:
    service = TechniqueFilterService()
    techniques = [
        _technique(
            technique_id="one",
            name="One",
            category="Google Dorks",
            description="First",
            tags=["first"],
        ),
        _technique(
            technique_id="two",
            name="Two",
            category="GitHub Search",
            description="Second",
            tags=["second"],
            engine="GitHub",
        ),
    ]

    filtered = service.filter(techniques, TechniqueFilterCriteria())

    assert [item.id for item in filtered] == ["one", "two"]


def test_filter_service_treats_search_text_as_case_insensitive_and_trimmed() -> None:
    service = TechniqueFilterService()
    techniques = [
        _technique(
            technique_id="github-actions",
            name="GitHub Actions Search",
            category="GitHub Search",
            description="Find public workflow references for a company.",
            tags=["github", "workflow"],
            engine="GitHub",
        )
    ]

    filtered = service.filter(
        techniques,
        TechniqueFilterCriteria(category_name="GitHub Search", search_text="  WORKFLOW  "),
    )

    assert [item.id for item in filtered] == ["github-actions"]


def test_filter_service_matches_multiple_search_terms_across_indexed_text() -> None:
    service = TechniqueFilterService()
    techniques = [
        _technique(
            technique_id="google-admin-login",
            name="Admin Login Search",
            category="Google Dorks",
            description="Find indexed admin login pages for a target.",
            tags=["google", "admin", "login"],
        ),
        _technique(
            technique_id="google-admin-panel",
            name="Admin Panel Search",
            category="Google Dorks",
            description="Find indexed admin panels for a target.",
            tags=["google", "admin"],
        ),
    ]

    filtered = service.filter(techniques, TechniqueFilterCriteria(search_text="admin login"))

    assert [item.id for item in filtered] == ["google-admin-login"]
