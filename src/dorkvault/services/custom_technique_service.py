"""Creation and persistence helpers for user-defined techniques."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Iterable, Mapping

from dorkvault.core.constants import APP_NAME
from dorkvault.core.exceptions import CustomTechniqueError
from dorkvault.core.models import Technique
from dorkvault.utils.json_storage import write_json_atomic
from dorkvault.utils.paths import get_user_techniques_dir

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class CustomTechniqueService:
    """Create validated custom techniques and persist them to a user JSON file."""

    def __init__(self, custom_file_path: Path | None = None) -> None:
        self.logger = logging.getLogger(APP_NAME)
        base_dir = get_user_techniques_dir()
        self.custom_file_path = custom_file_path or (base_dir / "custom_queries.json")
        self.custom_file_path.parent.mkdir(parents=True, exist_ok=True)

    def create_custom_technique(
        self,
        payload: Mapping[str, object],
        *,
        existing_ids: Iterable[str] | None = None,
    ) -> Technique:
        """Validate and persist a new custom technique."""
        file_payload = self._load_file_payload()
        raw_techniques = file_payload.setdefault("techniques", [])
        if not isinstance(raw_techniques, list):
            raise ValueError("Custom technique file has an invalid techniques list.")

        reserved_ids = {
            technique_id.strip()
            for technique_id in (existing_ids or [])
            if isinstance(technique_id, str) and technique_id.strip()
        }
        reserved_ids.update(
            str(item.get("id", "")).strip()
            for item in raw_techniques
            if isinstance(item, dict)
        )

        technique_record = self._normalize_payload(payload, reserved_ids=reserved_ids)
        technique = Technique.from_dict(
            technique_record,
            source_file=self.custom_file_path.name,
        )

        raw_techniques.append(technique_record)
        raw_techniques.sort(key=lambda item: str(item.get("name", "")).lower())
        self._save_file_payload(file_payload)
        self.logger.info(
            "Created custom technique.",
            extra={
                "event": "custom_technique_created",
                "technique_id": technique.id,
                "custom_file_path": str(self.custom_file_path),
            },
        )
        return technique

    def update_custom_technique(self, technique_id: str, payload: Mapping[str, object]) -> Technique:
        """Validate and persist edits for an existing custom technique."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            raise ValueError("Technique ID is required to update a custom technique.")

        file_payload = self._load_file_payload()
        raw_techniques = file_payload.setdefault("techniques", [])
        if not isinstance(raw_techniques, list):
            raise ValueError("Custom technique file has an invalid techniques list.")

        record_index, existing_record = self._find_custom_record(raw_techniques, normalized_id)
        if existing_record is None:
            raise ValueError("Only user-created custom techniques can be edited.")

        technique_record = self._normalize_payload(
            payload,
            reserved_ids=set(),
            technique_id=normalized_id,
        )
        technique = Technique.from_dict(
            technique_record,
            source_file=self.custom_file_path.name,
        )

        raw_techniques[record_index] = technique_record
        raw_techniques.sort(key=lambda item: str(item.get("name", "")).lower())
        self._save_file_payload(file_payload)
        self.logger.info(
            "Updated custom technique.",
            extra={
                "event": "custom_technique_updated",
                "technique_id": technique.id,
                "custom_file_path": str(self.custom_file_path),
            },
        )
        return technique

    def delete_custom_technique(self, technique_id: str) -> None:
        """Delete a user-created custom technique."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            raise ValueError("Technique ID is required to delete a custom technique.")

        file_payload = self._load_file_payload()
        raw_techniques = file_payload.setdefault("techniques", [])
        if not isinstance(raw_techniques, list):
            raise ValueError("Custom technique file has an invalid techniques list.")

        record_index, _record = self._find_custom_record(raw_techniques, normalized_id)
        if record_index == -1:
            raise ValueError("Only user-created custom techniques can be deleted.")

        del raw_techniques[record_index]
        self._save_file_payload(file_payload)
        self.logger.info(
            "Deleted custom technique.",
            extra={
                "event": "custom_technique_deleted",
                "technique_id": normalized_id,
                "custom_file_path": str(self.custom_file_path),
            },
        )

    def is_custom_technique(self, technique: Technique | str | None) -> bool:
        """Return whether a technique belongs to the user custom file."""
        if technique is None:
            return False
        if isinstance(technique, Technique):
            return technique.source_file == self.custom_file_path.name
        return self._find_custom_record(self._load_file_payload().get("techniques", []), technique.strip())[0] != -1

    def _normalize_payload(
        self,
        payload: Mapping[str, object],
        *,
        reserved_ids: set[str],
        technique_id: str | None = None,
    ) -> dict[str, object]:
        name = str(payload.get("name", "")).strip()
        category = str(payload.get("category", "")).strip()
        engine = str(payload.get("engine", "")).strip()
        description = str(payload.get("description", "")).strip()
        query_template = str(payload.get("query_template", "")).strip()
        example = str(payload.get("example", "")).strip()

        variables = self._normalize_list(payload.get("variables"))
        tags = self._normalize_list(payload.get("tags"))

        generated_id = technique_id or self._generate_unique_id(
            name=name,
            category=category,
            reserved_ids=reserved_ids,
        )

        return {
            "id": generated_id,
            "name": name,
            "category": category,
            "engine": engine,
            "description": description,
            "query_template": query_template,
            "variables": variables,
            "tags": tags,
            "example": example,
            "safe_mode": True,
            "reference": "Custom technique",
        }

    @staticmethod
    def _find_custom_record(raw_techniques: object, technique_id: str) -> tuple[int, dict[str, object] | None]:
        if not isinstance(raw_techniques, list):
            return -1, None

        for index, item in enumerate(raw_techniques):
            if not isinstance(item, dict):
                continue
            if str(item.get("id", "")).strip() == technique_id:
                return index, item
        return -1, None

    def _load_file_payload(self) -> dict[str, object]:
        if not self.custom_file_path.exists():
            self.logger.info(
                "No custom technique file found. Using an empty custom technique catalog.",
                extra={
                    "event": "custom_technique_file_missing",
                    "custom_file_path": str(self.custom_file_path),
                },
            )
            return self._default_file_payload()

        try:
            with self.custom_file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self.logger.warning(
                "Custom technique file contains invalid JSON.",
                extra={
                    "event": "custom_technique_invalid_json",
                    "custom_file_path": str(self.custom_file_path),
                    "error": str(exc),
                },
            )
            raise CustomTechniqueError(
                "The custom technique file is invalid. Fix or remove it before editing custom techniques."
            ) from exc
        except OSError as exc:
            self.logger.warning(
                "Custom technique file could not be read.",
                extra={
                    "event": "custom_technique_read_failed",
                    "custom_file_path": str(self.custom_file_path),
                    "error": str(exc),
                },
            )
            raise CustomTechniqueError("The custom technique file could not be read.") from exc

        if not isinstance(payload, dict):
            self.logger.warning(
                "Custom technique file payload is not an object.",
                extra={
                    "event": "custom_technique_payload_invalid",
                    "custom_file_path": str(self.custom_file_path),
                    "payload_type": type(payload).__name__,
                },
            )
            raise CustomTechniqueError("The custom technique file must contain a JSON object.")
        return payload

    def _save_file_payload(self, payload: dict[str, object]) -> None:
        try:
            write_json_atomic(self.custom_file_path, payload)
        except OSError as exc:
            self.logger.exception(
                "Custom techniques could not be saved.",
                extra={
                    "event": "custom_technique_save_failed",
                    "custom_file_path": str(self.custom_file_path),
                    "error": str(exc),
                },
            )
            raise CustomTechniqueError("Custom techniques could not be saved.") from exc

    @staticmethod
    def _default_file_payload() -> dict[str, object]:
        return {
            "category_id": "custom_queries",
            "category_name": "Custom Queries",
            "description": "User-created query techniques.",
            "display_order": 900,
            "techniques": [],
        }

    @staticmethod
    def _normalize_list(raw_value: object) -> list[str]:
        if isinstance(raw_value, str):
            values = raw_value.split(",")
        elif isinstance(raw_value, list):
            values = raw_value
        else:
            values = []

        return [
            str(item).strip()
            for item in values
            if str(item).strip()
        ]

    @staticmethod
    def _generate_unique_id(*, name: str, category: str, reserved_ids: set[str]) -> str:
        base_parts = [category.strip().lower(), name.strip().lower()]
        base_slug = "-".join(
            _SLUG_PATTERN.sub("-", part).strip("-")
            for part in base_parts
            if part.strip()
        ).strip("-")
        if not base_slug:
            base_slug = "custom-technique"

        candidate = base_slug
        suffix = 2
        while candidate in reserved_ids:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate
