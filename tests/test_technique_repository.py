from dorkvault.services.technique_repository import TechniqueRepository


def test_repository_loads_categories_and_techniques() -> None:
    repository = TechniqueRepository()
    categories = repository.load()
    techniques = repository.all_techniques()

    assert categories
    assert len(categories) >= 9
    assert len(techniques) >= 18
    assert len({technique.id for technique in techniques}) == len(techniques)
    assert all(technique.engine for technique in techniques)
    assert any(name in {"domain", "company", "keyword"} for technique in techniques for name in technique.variable_names)
    assert repository.category_groups()
    assert sum(len(group.categories) for group in repository.category_groups()) == len(categories)


def test_filtering_by_category_and_search() -> None:
    repository = TechniqueRepository()
    repository.load()

    google_results = repository.filter_techniques(category_name="Google Dorks")
    github_results = repository.filter_techniques(search_text="workflow")
    combined_results = repository.filter_techniques(category_name="GitHub Search", search_text="workflow")

    assert google_results
    assert all(item.category == "Google Dorks" for item in google_results)
    assert github_results
    assert any("workflow" in item.name.lower() or "workflow" in item.description.lower() for item in github_results)
    assert combined_results
    assert all(item.category == "GitHub Search" for item in combined_results)
    assert all("workflow" in item.search_text() for item in combined_results)


def test_repository_uses_cached_category_lookups_for_category_filters() -> None:
    repository = TechniqueRepository()
    repository.load()

    google_results = repository.filter_techniques(category_name="Google Dorks", search_text="admin login")

    assert google_results
    assert all(item.category == "Google Dorks" for item in google_results)
    assert all("admin" in item.search_text() and "login" in item.search_text() for item in google_results)
