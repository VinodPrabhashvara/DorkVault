import json

from dorkvault.services.recent_history_service import RecentHistoryService


def test_recent_history_service_persists_order_and_deduplicates(tmp_path) -> None:
    history_path = tmp_path / "recents.json"
    service = RecentHistoryService(history_path=history_path, max_items=5)

    assert service.all_ids() == []
    assert service.record_view("google-login-pages") == ["google-login-pages"]
    assert service.record_view("github-workflow-files") == [
        "github-workflow-files",
        "google-login-pages",
    ]
    assert service.record_view("google-login-pages") == [
        "google-login-pages",
        "github-workflow-files",
    ]

    persisted_payload = json.loads(history_path.read_text(encoding="utf-8"))
    assert persisted_payload == {
        "recents": ["google-login-pages", "github-workflow-files"]
    }

    reloaded_service = RecentHistoryService(history_path=history_path, max_items=5)
    assert reloaded_service.all_ids() == [
        "google-login-pages",
        "github-workflow-files",
    ]


def test_recent_history_service_caps_history_length(tmp_path) -> None:
    history_path = tmp_path / "recents.json"
    service = RecentHistoryService(history_path=history_path, max_items=3)

    service.record_view("one")
    service.record_view("two")
    service.record_view("three")
    service.record_view("four")

    assert service.all_ids() == ["four", "three", "two"]


def test_recent_history_service_migrates_legacy_settings_recents(tmp_path) -> None:
    history_path = tmp_path / "recents.json"
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "theme": "light",
                "last_target": "",
                "favorites": [],
                "recents": ["alpha", "beta", "alpha", "gamma"],
            }
        ),
        encoding="utf-8",
    )

    service = RecentHistoryService(
        history_path=history_path,
        legacy_settings_path=settings_path,
        max_items=5,
    )

    assert service.load() == ["alpha", "beta", "gamma"]
    assert json.loads(history_path.read_text(encoding="utf-8")) == {
        "recents": ["alpha", "beta", "gamma"]
    }


def test_recent_history_service_remove_cleans_existing_entry(tmp_path) -> None:
    history_path = tmp_path / "recents.json"
    service = RecentHistoryService(history_path=history_path, max_items=5)
    service.save(["alpha", "beta", "gamma"])

    assert service.remove("beta") == ["alpha", "gamma"]
    assert service.all_ids() == ["alpha", "gamma"]
