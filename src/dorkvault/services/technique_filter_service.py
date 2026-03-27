"""Filtering helpers for technique collections."""

from __future__ import annotations

from dataclasses import dataclass

from dorkvault.core.constants import ALL_TECHNIQUES_LABEL
from dorkvault.core.models import Technique


@dataclass(slots=True, frozen=True)
class TechniqueFilterCriteria:
    """Normalized filter criteria for technique searches."""

    category_name: str = ALL_TECHNIQUES_LABEL
    search_text: str = ""

    @property
    def normalized_category_name(self) -> str:
        return (self.category_name or ALL_TECHNIQUES_LABEL).strip()

    @property
    def normalized_search_text(self) -> str:
        return self.search_text.strip().lower()

    @property
    def normalized_search_terms(self) -> tuple[str, ...]:
        return tuple(term for term in self.normalized_search_text.split() if term)


class TechniqueFilterService:
    """Apply text and category filters to a technique collection."""

    def filter(
        self,
        techniques: list[Technique],
        criteria: TechniqueFilterCriteria | None = None,
    ) -> list[Technique]:
        active_criteria = criteria or TechniqueFilterCriteria()
        category_name = active_criteria.normalized_category_name
        search_terms = active_criteria.normalized_search_terms

        filtered: list[Technique] = []
        for technique in techniques:
            if category_name != ALL_TECHNIQUES_LABEL and technique.category != category_name:
                continue

            if search_terms and not all(term in technique.search_text() for term in search_terms):
                continue

            filtered.append(technique)

        return filtered
