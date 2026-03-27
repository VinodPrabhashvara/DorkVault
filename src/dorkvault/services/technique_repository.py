"""Load and query technique definitions from bundled JSON data."""

from __future__ import annotations

from pathlib import Path

from dorkvault.core.exceptions import DataValidationError
from dorkvault.core.constants import ALL_TECHNIQUES_LABEL
from dorkvault.core.models import Technique, TechniqueCategory, TechniqueCategoryGroup
from dorkvault.services.technique_filter_service import TechniqueFilterCriteria, TechniqueFilterService
from dorkvault.services.technique_loader import (
    DEFAULT_CATEGORY_GROUP_ID,
    TechniqueLoadResult,
    TechniqueLoader,
    TechniqueLoaderConfig,
)
from dorkvault.utils.paths import get_data_dir, get_user_techniques_dir


class TechniqueRepository:
    """Repository that loads techniques from JSON files and supports filtering."""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        custom_data_dir: Path | None = None,
        skip_invalid_entries: bool = False,
    ) -> None:
        self.data_dir = data_dir or (get_data_dir() / "techniques")
        self.custom_data_dir = custom_data_dir or get_user_techniques_dir()
        self.loader = TechniqueLoader(
            self.data_dir,
            config=TechniqueLoaderConfig(skip_invalid_entries=skip_invalid_entries),
        )
        self.custom_loader = TechniqueLoader(
            self.custom_data_dir,
            config=TechniqueLoaderConfig(skip_invalid_entries=skip_invalid_entries),
        )
        self.filter_service = TechniqueFilterService()
        self._all_techniques: list[Technique] = []
        self._categories: list[TechniqueCategory] = []
        self._category_groups: list[TechniqueCategoryGroup] = []
        self._techniques_by_id: dict[str, Technique] = {}
        self._techniques_by_category: dict[str, list[Technique]] = {}
        self._counts_by_category: dict[str, int] = {ALL_TECHNIQUES_LABEL: 0}

    def load(self) -> list[TechniqueCategory]:
        built_in_result = self.loader.load()
        custom_result = self._load_custom_result()
        merged_result = self._merge_results(built_in_result, custom_result)
        self._all_techniques = list(merged_result.techniques)
        self._categories = self._build_categories(merged_result)
        self._category_groups = self._build_category_groups(self._categories)
        self._techniques_by_id = {technique.id: technique for technique in self._all_techniques}
        self._techniques_by_category = {
            category.name: list(category.techniques)
            for category in self._categories
        }
        self._counts_by_category = {
            ALL_TECHNIQUES_LABEL: len(self._all_techniques),
            **{
                category.name: len(category.techniques)
                for category in self._categories
            },
        }
        return self._categories

    def categories(self) -> list[TechniqueCategory]:
        return self._categories or self.load()

    def category_groups(self) -> list[TechniqueCategoryGroup]:
        if not self._category_groups:
            self.load()
        return self._category_groups

    def all_techniques(self) -> list[Technique]:
        if not self._all_techniques:
            self.load()
        return self._all_techniques

    def get(self, technique_id: str) -> Technique | None:
        if not self._techniques_by_id:
            self.load()
        return self._techniques_by_id.get(technique_id)

    def category_names(self) -> list[str]:
        return [ALL_TECHNIQUES_LABEL, *[category.name for category in self.categories()]]

    def engine_names(self) -> list[str]:
        """Return distinct engine names in sorted order."""
        return sorted({technique.engine for technique in self.all_techniques() if technique.engine})

    def filter_techniques(
        self,
        category_name: str = ALL_TECHNIQUES_LABEL,
        search_text: str = "",
    ) -> list[Technique]:
        source_techniques = self.techniques_for_category(category_name)
        normalized_category = (
            ALL_TECHNIQUES_LABEL if category_name != ALL_TECHNIQUES_LABEL else category_name
        )
        return self.filter_service.filter(
            source_techniques,
            TechniqueFilterCriteria(category_name=normalized_category, search_text=search_text),
        )

    def counts_by_category(self) -> dict[str, int]:
        if not self._all_techniques:
            self.load()
        return dict(self._counts_by_category)

    def techniques_for_category(self, category_name: str) -> list[Technique]:
        if not self._techniques_by_category:
            self.load()
        if not category_name or category_name == ALL_TECHNIQUES_LABEL:
            return self.all_techniques()
        return list(self._techniques_by_category.get(category_name, []))

    def techniques_for_ids(
        self,
        technique_ids: list[str] | tuple[str, ...] | set[str],
        *,
        preserve_order: bool = False,
    ) -> list[Technique]:
        if not self._techniques_by_id:
            self.load()

        if preserve_order:
            return [
                self._techniques_by_id[technique_id]
                for technique_id in technique_ids
                if technique_id in self._techniques_by_id
            ]

        techniques = [
            self._techniques_by_id[technique_id]
            for technique_id in technique_ids
            if technique_id in self._techniques_by_id
        ]
        techniques.sort(key=lambda item: item.name.lower())
        return techniques

    def _load_custom_result(self) -> TechniqueLoadResult:
        if not self.custom_data_dir.exists():
            return TechniqueLoadResult()
        if not any(self.custom_data_dir.rglob("*.json")):
            return TechniqueLoadResult()
        return self.custom_loader.load()

    @staticmethod
    def _merge_results(
        built_in_result: TechniqueLoadResult,
        custom_result: TechniqueLoadResult,
    ) -> TechniqueLoadResult:
        techniques_by_id: dict[str, Technique] = {}

        for technique in built_in_result.techniques:
            techniques_by_id[technique.id] = technique

        for technique in custom_result.techniques:
            existing = techniques_by_id.get(technique.id)
            if existing is not None:
                raise DataValidationError(
                    f"duplicate technique id '{technique.id}' already loaded from {existing.source_file}; "
                    f"conflict in {technique.source_file}"
                )
            techniques_by_id[technique.id] = technique

        return TechniqueLoadResult(
            categories=[*built_in_result.categories, *custom_result.categories],
            techniques=sorted(techniques_by_id.values(), key=lambda item: item.name.lower()),
            loaded_files=[*built_in_result.loaded_files, *custom_result.loaded_files],
            skipped_entries=built_in_result.skipped_entries + custom_result.skipped_entries,
        )

    @staticmethod
    def _build_categories(load_result: TechniqueLoadResult) -> list[TechniqueCategory]:
        category_metadata: dict[str, TechniqueCategory] = {}
        inferred_metadata: dict[str, TechniqueCategory] = {}
        grouped_techniques: dict[str, list[Technique]] = {}
        for category in load_result.categories:
            existing_category = category_metadata.get(category.name)
            if existing_category is None:
                category_metadata[category.name] = category
            else:
                TechniqueRepository._ensure_compatible_category_metadata(existing_category, category)

            for technique in category.techniques:
                grouped_techniques.setdefault(technique.category, []).append(technique)
                if technique.category == category.name:
                    continue

                existing_inferred = inferred_metadata.get(technique.category)
                inferred_category = TechniqueCategory(
                    id=technique.category.lower().replace(" ", "_"),
                    name=technique.category,
                    description=f"{technique.category} techniques.",
                    display_order=category.display_order,
                    group_id=category.group_id,
                    group_name=category.group_name,
                    group_description=category.group_description,
                    group_display_order=category.group_display_order,
                )
                if existing_inferred is None:
                    inferred_metadata[technique.category] = inferred_category
                else:
                    TechniqueRepository._ensure_compatible_category_metadata(
                        existing_inferred,
                        inferred_category,
                    )

        categories: list[TechniqueCategory] = []
        for category_name, techniques in grouped_techniques.items():
            existing_category = category_metadata.get(category_name) or inferred_metadata.get(category_name)
            categories.append(
                TechniqueCategory(
                    id=(
                        existing_category.id
                        if existing_category is not None
                        else category_name.lower().replace(" ", "_")
                    ),
                    name=category_name,
                    description=(
                        existing_category.description
                        if existing_category is not None
                        else f"{category_name} techniques."
                    ),
                    display_order=existing_category.display_order if existing_category is not None else 900,
                    group_id=existing_category.group_id if existing_category is not None else "",
                    group_name=existing_category.group_name if existing_category is not None else "",
                    group_description=(
                        existing_category.group_description
                        if existing_category is not None
                        else ""
                    ),
                    group_display_order=(
                        existing_category.group_display_order
                        if existing_category is not None
                        else 900
                    ),
                    techniques=sorted(techniques, key=lambda item: item.name.lower()),
                )
            )

        categories.sort(key=lambda item: (item.display_order, item.name.lower()))
        return categories

    @staticmethod
    def _build_category_groups(categories: list[TechniqueCategory]) -> list[TechniqueCategoryGroup]:
        groups_by_id: dict[str, TechniqueCategoryGroup] = {}
        for category in categories:
            group_id = category.group_id or DEFAULT_CATEGORY_GROUP_ID
            group_name = category.group_name or ""
            existing_group = groups_by_id.get(group_id)
            if existing_group is None:
                groups_by_id[group_id] = TechniqueCategoryGroup(
                    id=group_id,
                    name=group_name,
                    description=category.group_description,
                    display_order=category.group_display_order,
                    categories=[category],
                )
                continue

            if group_name and existing_group.name and group_name != existing_group.name:
                raise DataValidationError(
                    f"category group '{group_id}' uses inconsistent names: "
                    f"'{existing_group.name}' and '{group_name}'"
                )

            if (
                category.group_display_order != existing_group.display_order
                and group_id != DEFAULT_CATEGORY_GROUP_ID
            ):
                raise DataValidationError(
                    f"category group '{group_id}' uses inconsistent display_order values."
                )

            if not existing_group.name and group_name:
                existing_group.name = group_name
            if not existing_group.description and category.group_description:
                existing_group.description = category.group_description
            existing_group.categories.append(category)

        groups = list(groups_by_id.values())
        for group in groups:
            group.categories.sort(key=lambda item: (item.display_order, item.name.lower()))

        groups.sort(key=lambda item: (item.display_order, item.name.lower()))
        return groups

    @staticmethod
    def _ensure_compatible_category_metadata(
        existing_category: TechniqueCategory,
        incoming_category: TechniqueCategory,
    ) -> None:
        if existing_category.id != incoming_category.id:
            raise DataValidationError(
                f"category '{existing_category.name}' is defined with conflicting ids: "
                f"'{existing_category.id}' and '{incoming_category.id}'"
            )

        if existing_category.group_id != incoming_category.group_id:
            raise DataValidationError(
                f"category '{existing_category.name}' is assigned to multiple groups."
            )
