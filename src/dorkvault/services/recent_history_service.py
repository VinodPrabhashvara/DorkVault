"""Persistence and ordering for recently viewed techniques."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dorkvault.core.constants import APP_NAME
from dorkvault.core.exceptions import RecentHistoryError
from dorkvault.utils.json_storage import write_json_atomic
from dorkvault.utils.paths import get_user_data_dir


class RecentHistoryService:
    """Load, persist, and update recently viewed technique identifiers."""

    def __init__(
        self,
        history_path: Path | None = None,
        *,
        legacy_settings_path: Path | None = None,
        max_items: int = 25,
    ) -> None:
        self.logger = logging.getLogger(APP_NAME)
        self.history_path = history_path or (get_user_data_dir() / "recents.json")
        self.legacy_settings_path = legacy_settings_path
        self.max_items = max(1, max_items)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._recent_ids: list[str] | None = None

    def all_ids(self) -> list[str]:
        """Return recent technique IDs in most-recent-first order."""
        return list(self._load_state())

    def record_view(self, technique_id: str) -> list[str]:
        """Add a technique to recent history, moving it to the top if needed."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            raise ValueError("Technique ID is required to update recent history.")

        recent_ids = self._load_state()
        if recent_ids and recent_ids[0] == normalized_id:
            return list(recent_ids)

        updated_ids = [item for item in recent_ids if item != normalized_id]
        updated_ids.insert(0, normalized_id)
        updated_ids = updated_ids[: self.max_items]
        self.save(updated_ids)
        self.logger.info("Recorded recent technique view: %s", normalized_id)
        return list(updated_ids)

    def remove(self, technique_id: str) -> list[str]:
        """Remove a technique from recent history if present."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            return self.all_ids()

        updated_ids = [item for item in self._load_state() if item != normalized_id]
        if len(updated_ids) == len(self._load_state()):
            return list(updated_ids)

        self.save(updated_ids)
        self.logger.info("Removed recent technique during cleanup: %s", normalized_id)
        return list(updated_ids)

    def load(self) -> list[str]:
        """Load recent history from disk."""
        recent_ids = self._load_from_disk()
        self._recent_ids = recent_ids
        return list(recent_ids)

    def save(self, recent_ids: list[str] | None = None) -> None:
        """Persist recent history to disk."""
        active_ids = self._normalize_ids(recent_ids if recent_ids is not None else self._load_state())
        capped_ids = active_ids[: self.max_items]
        payload = {"recents": capped_ids}
        try:
            write_json_atomic(self.history_path, payload)
        except OSError as exc:
            self.logger.exception(
                "Recent history could not be saved.",
                extra={
                    "event": "recent_history_save_failed",
                    "history_path": str(self.history_path),
                    "error": str(exc),
                },
            )
            raise RecentHistoryError("Recent history could not be saved.") from exc
        self._recent_ids = capped_ids
        self.logger.info("Saved %s recent technique(s).", len(capped_ids))

    def _load_state(self) -> list[str]:
        if self._recent_ids is None:
            self._recent_ids = self._load_from_disk()
        return self._recent_ids

    def _load_from_disk(self) -> list[str]:
        if self.history_path.exists():
            try:
                with self.history_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (json.JSONDecodeError, OSError) as exc:
                self.logger.warning(
                    "Recent history file '%s' could not be read. Starting with an empty history. %s",
                    self.history_path,
                    exc,
                )
                return []

            recent_ids = self._extract_ids(payload)
            self.logger.info(
                "Loaded %s recent technique(s) from '%s'.",
                len(recent_ids),
                self.history_path,
            )
            return recent_ids

        legacy_ids = self._load_legacy_recents()
        if legacy_ids:
            self.logger.info(
                "Migrating %s recent technique(s) from legacy settings into '%s'.",
                len(legacy_ids),
                self.history_path,
            )
            try:
                self.save(legacy_ids)
            except RecentHistoryError:
                self.logger.exception(
                    "Legacy recent history could not be migrated to the dedicated history file.",
                    extra={
                        "event": "recent_history_migration_failed",
                        "history_path": str(self.history_path),
                    },
                )
            return list(legacy_ids)

        self.logger.info("No recent history file found. Starting with an empty history.")
        return []

    def _load_legacy_recents(self) -> list[str]:
        if self.legacy_settings_path is None or not self.legacy_settings_path.exists():
            return []

        try:
            with self.legacy_settings_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            self.logger.warning(
                "Legacy settings file '%s' could not be read during recent history migration. %s",
                self.legacy_settings_path,
                exc,
            )
            return []

        if not isinstance(payload, dict):
            return []
        return self._normalize_ids(payload.get("recents", []))

    def _extract_ids(self, payload: object) -> list[str]:
        if isinstance(payload, dict):
            raw_ids = payload.get("recents", [])
        else:
            raw_ids = payload
        return self._normalize_ids(raw_ids)

    @staticmethod
    def _normalize_ids(raw_ids: object) -> list[str]:
        if not isinstance(raw_ids, (list, tuple)):
            return []

        normalized_ids: list[str] = []
        seen_ids: set[str] = set()
        for item in raw_ids:
            if not isinstance(item, str):
                continue
            normalized_id = item.strip()
            if not normalized_id or normalized_id in seen_ids:
                continue
            normalized_ids.append(normalized_id)
            seen_ids.add(normalized_id)
        return normalized_ids
