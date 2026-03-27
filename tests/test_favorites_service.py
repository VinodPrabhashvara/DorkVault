import json

from dorkvault.services.favorites_service import FavoritesService


def test_favorites_service_persists_toggles_across_reloads(tmp_path) -> None:
    favorites_path = tmp_path / "favorites.json"
    service = FavoritesService(favorites_path=favorites_path)

    assert service.all_ids() == []
    assert service.toggle("google-login-pages") is True
    assert service.is_favorite("google-login-pages") is True

    persisted_payload = json.loads(favorites_path.read_text(encoding="utf-8"))
    assert persisted_payload == {"favorites": ["google-login-pages"]}

    reloaded_service = FavoritesService(favorites_path=favorites_path)
    assert reloaded_service.all_ids() == ["google-login-pages"]
    assert reloaded_service.toggle("google-login-pages") is False
    assert reloaded_service.all_ids() == []


def test_favorites_service_normalizes_saved_ids(tmp_path) -> None:
    favorites_path = tmp_path / "favorites.json"
    service = FavoritesService(favorites_path=favorites_path)

    service.save(["  zeta-technique  ", "alpha-technique", "alpha-technique", "", "   "])

    assert service.all_ids() == ["alpha-technique", "zeta-technique"]
    persisted_payload = json.loads(favorites_path.read_text(encoding="utf-8"))
    assert persisted_payload == {"favorites": ["alpha-technique", "zeta-technique"]}


def test_favorites_service_migrates_legacy_settings_favorites(tmp_path) -> None:
    favorites_path = tmp_path / "favorites.json"
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "theme": "light",
                "last_target": "",
                "favorites": ["github-workflow-files", "google-login-pages", "github-workflow-files"],
                "recents": [],
            }
        ),
        encoding="utf-8",
    )

    service = FavoritesService(
        favorites_path=favorites_path,
        legacy_settings_path=settings_path,
    )

    assert service.load() == ["github-workflow-files", "google-login-pages"]
    assert favorites_path.exists()

    persisted_payload = json.loads(favorites_path.read_text(encoding="utf-8"))
    assert persisted_payload == {
        "favorites": ["github-workflow-files", "google-login-pages"]
    }


def test_favorites_service_remove_cleans_existing_favorite(tmp_path) -> None:
    favorites_path = tmp_path / "favorites.json"
    service = FavoritesService(favorites_path=favorites_path)
    service.save(["google-login-pages", "github-workflow-files"])

    assert service.remove("google-login-pages") is True
    assert service.all_ids() == ["github-workflow-files"]
    assert service.remove("missing-technique") is False
