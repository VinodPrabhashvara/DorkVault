from __future__ import annotations

from pathlib import Path

from dorkvault.services.technique_filter_service import TechniqueFilterCriteria, TechniqueFilterService
from dorkvault.services.technique_loader import TechniqueLoader
from dorkvault.services.technique_repository import TechniqueRepository


def test_bundled_technique_catalogs_load_cleanly(bundled_techniques_dir) -> None:
    loader = TechniqueLoader(bundled_techniques_dir)

    result = loader.load()

    assert result.loaded_files
    assert result.skipped_entries == 0
    assert result.techniques
    expected_file_count = len(list(Path(bundled_techniques_dir).rglob("*.json")))
    assert len(result.categories) == expected_file_count
    assert len(result.loaded_files) == expected_file_count
    assert len(result.techniques) >= 1000
    assert all(len(category.techniques) >= 5 for category in result.categories)
    assert len({technique.id for technique in result.techniques}) == len(result.techniques)
    assert all(technique.source_file for technique in result.techniques)


def test_bundled_repository_category_counts_match_loaded_techniques(bundled_techniques_dir, tmp_path) -> None:
    repository = TechniqueRepository(
        data_dir=bundled_techniques_dir,
        custom_data_dir=tmp_path / "user-techniques",
    )

    categories = repository.load()
    counts = repository.counts_by_category()

    assert categories
    assert counts["All Techniques"] == len(repository.all_techniques())
    assert sum(len(category.techniques) for category in categories) == len(repository.all_techniques())
    assert all(counts[category.name] == len(category.techniques) for category in categories)


def test_bundled_catalog_search_and_filter_work_at_scale(bundled_techniques_dir) -> None:
    techniques = TechniqueLoader(bundled_techniques_dir).load().techniques
    service = TechniqueFilterService()

    filtered = service.filter(
        techniques,
        TechniqueFilterCriteria(category_name="GitHub Search", search_text="workflow"),
    )

    assert len(techniques) >= 1000
    assert filtered
    assert all(technique.category == "GitHub Search" for technique in filtered)
    assert all("workflow" in technique.search_text() for technique in filtered)
