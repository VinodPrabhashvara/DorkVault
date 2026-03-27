import sys

from dorkvault.core.constants import DEFAULT_THEME, THEME_DARK, THEME_LIGHT
from dorkvault.services.theme_manager import ThemeManager
from dorkvault.utils.paths import get_assets_dir, get_runtime_package_root
from dorkvault.utils.resource_loader import resolve_icon_path


def test_runtime_package_paths_resolve_from_pyinstaller_bundle(tmp_path, monkeypatch) -> None:
    bundle_root = tmp_path / "bundle"
    bundled_package_root = bundle_root / "dorkvault"
    (bundled_package_root / "assets" / "themes").mkdir(parents=True)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)

    assert get_runtime_package_root() == bundled_package_root
    assert get_assets_dir() == bundled_package_root / "assets"


def test_theme_manager_falls_back_to_default_theme(tmp_path) -> None:
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir(parents=True)
    (themes_dir / "light.qss").write_text("QWidget { color: black; }", encoding="utf-8")

    manager = ThemeManager(themes_dir=themes_dir)

    assert manager.load_theme("missing-theme") == "QWidget { color: black; }"
    assert manager.normalize_theme_name("missing-theme") == DEFAULT_THEME


def test_theme_manager_exposes_only_light_and_dark() -> None:
    manager = ThemeManager()

    assert manager.available_themes() == [THEME_LIGHT, THEME_DARK]
    assert manager.is_valid_theme(THEME_LIGHT) is True
    assert manager.is_valid_theme(THEME_DARK) is True
    assert manager.is_valid_theme("blue") is False


def test_resolve_icon_path_uses_fallback_icon(tmp_path, monkeypatch) -> None:
    bundle_root = tmp_path / "bundle"
    bundled_icons_dir = bundle_root / "dorkvault" / "assets" / "icons"
    bundled_icons_dir.mkdir(parents=True)
    fallback_icon = bundled_icons_dir / "app_icon.svg"
    fallback_icon.write_text("<svg></svg>", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)

    assert resolve_icon_path("missing_icon.svg") == fallback_icon
