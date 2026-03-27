"""Persistence and favorite state management for techniques."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from dorkvault.core.constants import APP_NAME
from dorkvault.core.exceptions import FavoritesError
from dorkvault.utils.json_storage import write_json_atomic
from dorkvault.utils.paths import get_user_data_dir


class FavoritesService:
    """Load, persist, and query favorited technique identifiers."""

    def __init__(
        self,
        favorites_path: Path | None = None,
        *,
        legacy_settings_path: Path | None = None,
    ) -> None:
        self.logger = logging.getLogger(APP_NAME)
        self.favorites_path = favorites_path or (get_user_data_dir() / "favorites.json")
        self.legacy_settings_path = legacy_settings_path
        self.favorites_path.parent.mkdir(parents=True, exist_ok=True)
        self._favorite_ids: set[str] | None = None

    def all_ids(self) -> list[str]:
        """Return sorted favorite IDs."""
        return sorted(self._load_state())

    def is_favorite(self, technique_id: str) -> bool:
        """Return whether the given technique is currently favorited."""
        return technique_id.strip() in self._load_state()

    def toggle(self, technique_id: str) -> bool:
        """Toggle favorite state and return the updated state."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            raise ValueError("Technique ID is required to update favorites.")

        favorite_ids = self._load_state()
        if normalized_id in favorite_ids:
            favorite_ids.remove(normalized_id)
            is_favorite = False
            self.logger.info("Removed favorite technique: %s", normalized_id)
        else:
            favorite_ids.add(normalized_id)
            is_favorite = True
            self.logger.info("Added favorite technique: %s", normalized_id)

        self.save(favorite_ids)
        return is_favorite

    def remove(self, technique_id: str) -> bool:
        """Remove a technique from favorites if present."""
        normalized_id = technique_id.strip()
        if not normalized_id:
            return False

        favorite_ids = self._load_state()
        if normalized_id not in favorite_ids:
            return False

        favorite_ids.remove(normalized_id)
        self.save(favorite_ids)
        self.logger.info("Removed favorite technique during cleanup: %s", normalized_id)
        return True

    def load(self) -> list[str]:
        """Load favorites from disk and return sorted IDs."""
        favorite_ids = self._load_from_disk()
        self._favorite_ids = favorite_ids
        return sorted(favorite_ids)

    def save(self, favorite_ids: Iterable[str] | None = None) -> None:
        """Persist favorites to disk."""
        active_ids = self._normalize_ids(favorite_ids if favorite_ids is not None else self._load_state())
        payload = {"favorites": active_ids}
        try:
            write_json_atomic(self.favorites_path, payload)
        except OSError as exc:
            self.logger.exception(
                "Favorites could not be saved.",
                extra={
                    "event": "favorites_save_failed",
                    "favorites_path": str(self.favorites_path),
                    "error": str(exc),
                },
            )
            raise FavoritesError("Favorites could not be saved.") from exc
        self._favorite_ids = set(active_ids)
        self.logger.info("Saved %s favorite technique(s).", len(active_ids))

    def _load_state(self) -> set[str]:
        if self._favorite_ids is None:
            self._favorite_ids = self._load_from_disk()
        return self._favorite_ids

    def _load_from_disk(self) -> set[str]:
        if self.favorites_path.exists():
            try:
                with self.favorites_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (json.JSONDecodeError, OSError) as exc:
                self.logger.warning(
                    "Favorites file '%s' could not be read. Starting with an empty favorites set. %s",
                    self.favorites_path,
                    exc,
                )
                return set()

            favorite_ids = self._extract_ids(payload)
            self.logger.info(
                "Loaded %s favorite technique(s) from '%s'.",
                len(favorite_ids),
                self.favorites_path,
            )
            return favorite_ids

        legacy_ids = self._load_legacy_favorites()
        if legacy_ids:
            self.logger.info(
                "Migrating %s favorite technique(s) from legacy settings into '%s'.",
                len(legacy_ids),
                self.favorites_path,
            )
            try:
                self.save(legacy_ids)
            except FavoritesError:
                self.logger.exception(
                    "Legacy favorites could not be migrated to the dedicated favorites file.",
                    extra={
                        "event": "favorites_migration_failed",
                        "favorites_path": str(self.favorites_path),
                    },
                )
            return set(legacy_ids)

        self.logger.info("No favorites file found. Starting with an empty favorites set.")
        return set()

    def _load_legacy_favorites(self) -> list[str]:
        if self.legacy_settings_path is None or not self.legacy_settings_path.exists():
            return []

        try:
            with self.legacy_settings_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            self.logger.warning(
                "Legacy settings file '%s' could not be read during favorites migration. %s",
                self.legacy_settings_path,
                exc,
            )
            return []

        if not isinstance(payload, dict):
            return []
        return self._normalize_ids(payload.get("favorites", []))

    def _extract_ids(self, payload: object) -> set[str]:
        if isinstance(payload, dict):
            raw_ids = payload.get("favorites", [])
        else:
            raw_ids = payload
        return set(self._normalize_ids(raw_ids))

    @staticmethod
    def _normalize_ids(raw_ids: object) -> list[str]:
        if not isinstance(raw_ids, (list, tuple, set)):
            return []

        return sorted(
            {
                str(item).strip()
                for item in raw_ids
                if isinstance(item, str) and str(item).strip()
            }
        )
