"""Load and validate JSON technique catalogs from disk."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from dorkvault.core.exceptions import DataValidationError, TechniqueLoadError
from dorkvault.core.models import Technique, TechniqueCategory
from dorkvault.utils.paths import get_data_dir

DEFAULT_CATEGORY_GROUP_ID = "default"
DEFAULT_CATEGORY_GROUP_NAME = "Categories"
DEFAULT_CATEGORY_GROUP_ORDER = 900


@dataclass(slots=True, frozen=True)
class TechniqueLoaderConfig:
    """Runtime options for technique loading behavior."""

    skip_invalid_entries: bool = False


@dataclass(slots=True)
class TechniqueLoadResult:
    """Validated in-memory technique data loaded from one or more files."""

    categories: list[TechniqueCategory] = field(default_factory=list)
    techniques: list[Technique] = field(default_factory=list)
    loaded_files: list[str] = field(default_factory=list)
    skipped_entries: int = 0


class TechniqueLoader:
    """Load grouped technique JSON files into validated in-memory models."""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        config: TechniqueLoaderConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.data_dir = data_dir or (get_data_dir() / "techniques")
        self.config = config or TechniqueLoaderConfig()
        self.logger = logger or logging.getLogger(__name__)

    def load(self) -> TechniqueLoadResult:
        """Load all technique catalogs from the configured directory."""
        if not self.data_dir.exists():
            raise TechniqueLoadError(f"Technique data directory not found: {self.data_dir}")

        json_files = sorted(
            self.data_dir.rglob("*.json"),
            key=lambda item: item.relative_to(self.data_dir).as_posix().lower(),
        )
        if not json_files:
            self.logger.warning("No technique JSON files found in %s", self.data_dir)
            return TechniqueLoadResult()

        self.logger.info("Loading %d technique file(s) from %s", len(json_files), self.data_dir)

        result = TechniqueLoadResult()
        techniques_by_id: dict[str, Technique] = {}

        for json_path in json_files:
            relative_source = json_path.relative_to(self.data_dir).as_posix()
            category, skipped_from_file = self._load_category(
                json_path,
                relative_source=relative_source,
                techniques_by_id=techniques_by_id,
            )
            result.categories.append(category)
            result.loaded_files.append(relative_source)
            result.skipped_entries += skipped_from_file

            for technique in category.techniques:
                techniques_by_id[technique.id] = technique

        result.categories.sort(key=lambda item: (item.display_order, item.name.lower()))
        result.techniques = sorted(techniques_by_id.values(), key=lambda item: item.name.lower())

        self.logger.info(
            "Loaded %d technique(s) across %d file(s); skipped %d invalid entries.",
            len(result.techniques),
            len(result.loaded_files),
            result.skipped_entries,
        )
        return result

    def _load_category(
        self,
        json_path: Path,
        *,
        relative_source: str,
        techniques_by_id: dict[str, Technique],
    ) -> tuple[TechniqueCategory, int]:
        payload = self._read_json(json_path)

        category_id = str(payload.get("category_id", "")).strip()
        category_name = str(payload.get("category_name", "")).strip()
        description = str(payload.get("description", "")).strip()
        display_order = self._parse_display_order(
            payload=payload,
            field_name="display_order",
            source_file=relative_source,
            default=100,
        )
        group_id, group_name, group_description, group_display_order = self._resolve_group_metadata(
            json_path=json_path,
            payload=payload,
            relative_source=relative_source,
        )
        raw_techniques = payload.get("techniques", [])

        if not category_id or not category_name:
            raise DataValidationError(f"{relative_source} is missing category metadata.")
        if not isinstance(raw_techniques, list):
            raise DataValidationError(f"{relative_source} has an invalid techniques list.")

        valid_techniques: list[Technique] = []
        skipped_entries = 0

        for index, item in enumerate(raw_techniques, start=1):
            if not isinstance(item, dict):
                skipped_entries += self._handle_invalid_entry(
                    message=f"{relative_source} entry #{index} must be an object.",
                )
                continue

            try:
                technique = Technique.from_dict(
                    item,
                    default_category=category_name,
                    source_file=relative_source,
                )
                self._ensure_unique_technique_id(
                    technique=technique,
                    techniques_by_id=techniques_by_id,
                    source_file=relative_source,
                    index=index,
                )
            except ValueError as exc:
                skipped_entries += self._handle_invalid_entry(
                    message=f"{relative_source} entry #{index} is invalid: {exc}",
                )
                continue

            if not bool(item.get("enabled", True)):
                self.logger.info(
                    "Skipping disabled technique '%s' from %s entry #%d.",
                    technique.id,
                    relative_source,
                    index,
                    extra={
                        "event": "technique_disabled_skipped",
                        "source_file": relative_source,
                        "technique_id": technique.id,
                        "entry_index": index,
                    },
                )
                continue

            valid_techniques.append(technique)

        valid_techniques.sort(key=lambda item: item.name.lower())
        self.logger.info(
            "Loaded %d technique(s) from %s.",
            len(valid_techniques),
            relative_source,
            extra={
                "event": "technique_file_loaded",
                "source_file": relative_source,
                "technique_count": len(valid_techniques),
                "skipped_entries": skipped_entries,
            },
        )
        return (
            TechniqueCategory(
                id=category_id,
                name=category_name,
                description=description,
                display_order=display_order,
                group_id=group_id,
                group_name=group_name,
                group_description=group_description,
                group_display_order=group_display_order,
                techniques=valid_techniques,
            ),
            skipped_entries,
        )

    def _read_json(self, json_path: Path) -> dict:
        try:
            with json_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self.logger.error(
                "Technique file contains invalid JSON.",
                extra={
                    "event": "technique_json_invalid",
                    "source_file": json_path.name,
                    "error": str(exc),
                },
            )
            raise TechniqueLoadError(f"Invalid JSON in {json_path.name}: {exc}") from exc
        except OSError as exc:
            self.logger.error(
                "Technique file could not be read.",
                extra={
                    "event": "technique_read_failed",
                    "source_file": json_path.name,
                    "error": str(exc),
                },
            )
            raise TechniqueLoadError(f"Unable to read {json_path.name}: {exc}") from exc

        if not isinstance(payload, dict):
            self.logger.error(
                "Technique file must contain a top-level JSON object.",
                extra={
                    "event": "technique_json_payload_invalid",
                    "source_file": json_path.name,
                    "payload_type": type(payload).__name__,
                },
            )
            raise TechniqueLoadError(f"{json_path.name} must contain a JSON object at the top level.")
        return payload

    def _ensure_unique_technique_id(
        self,
        *,
        technique: Technique,
        techniques_by_id: dict[str, Technique],
        source_file: str,
        index: int,
    ) -> None:
        existing = techniques_by_id.get(technique.id)
        if existing is None:
            return

        raise ValueError(
            f"duplicate technique id '{technique.id}' already loaded from {existing.source_file}; "
            f"conflict in {source_file} entry #{index}"
        )

    def _handle_invalid_entry(self, *, message: str) -> int:
        if self.config.skip_invalid_entries:
            self.logger.warning(
                "Skipping invalid technique entry: %s",
                message,
                extra={
                    "event": "technique_entry_skipped",
                    "reason": message,
                },
            )
            return 1
        raise DataValidationError(message)

    def _parse_display_order(
        self,
        *,
        payload: dict,
        field_name: str,
        source_file: str,
        default: int,
    ) -> int:
        try:
            return int(payload.get(field_name, default))
        except (TypeError, ValueError) as exc:
            raise DataValidationError(f"{source_file} has an invalid {field_name} value.") from exc

    def _resolve_group_metadata(
        self,
        *,
        json_path: Path,
        payload: dict,
        relative_source: str,
    ) -> tuple[str, str, str, int]:
        group_id = self._first_non_empty_string(payload, "category_group_id", "group_id")
        group_name = self._first_non_empty_string(payload, "category_group_name", "group_name")
        group_description = self._first_non_empty_string(
            payload,
            "category_group_description",
            "group_description",
        )

        group_display_order = self._parse_display_order(
            payload=payload,
            field_name="category_group_display_order",
            source_file=relative_source,
            default=DEFAULT_CATEGORY_GROUP_ORDER,
        )
        if "category_group_display_order" not in payload and "group_display_order" in payload:
            group_display_order = self._parse_display_order(
                payload={"group_display_order": payload.get("group_display_order")},
                field_name="group_display_order",
                source_file=relative_source,
                default=DEFAULT_CATEGORY_GROUP_ORDER,
            )

        parent = json_path.relative_to(self.data_dir).parent
        if parent != Path("."):
            fallback_id = "_".join(part.strip().lower() for part in parent.parts if part.strip())
            fallback_name = " / ".join(self._display_name_from_segment(part) for part in parent.parts if part.strip())
            group_id = group_id or fallback_id
            group_name = group_name or fallback_name

        return (
            group_id or DEFAULT_CATEGORY_GROUP_ID,
            group_name or DEFAULT_CATEGORY_GROUP_NAME,
            group_description,
            group_display_order,
        )

    @staticmethod
    def _first_non_empty_string(payload: dict, *field_names: str) -> str:
        for field_name in field_names:
            value = str(payload.get(field_name, "")).strip()
            if value:
                return value
        return ""

    @staticmethod
    def _display_name_from_segment(segment: str) -> str:
        return segment.replace("-", " ").replace("_", " ").strip().title()
