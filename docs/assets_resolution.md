# Asset And Icon Resolution

DorkVault resolves themes, icons, and bundled data through shared path helpers so the app works the same way in development and in a packaged build.

## Runtime Resolution

- In development, assets are loaded from `src/dorkvault/assets`.
- In a PyInstaller build, assets are loaded from `sys._MEIPASS/dorkvault/assets`.
- Bundled data files follow the same rule under `dorkvault/data`.
- Writable user files such as settings, favorites, and recents are not stored beside the executable. They continue to live in the per-user data directory returned by `get_user_data_dir()`.

## Utilities

- `dorkvault.utils.paths.get_runtime_package_root()` resolves the active package root for source or bundled mode.
- `dorkvault.utils.paths.get_assets_dir()` and `get_data_dir()` build on that runtime-aware root.
- `dorkvault.utils.resource_loader.load_theme()` loads a requested theme and falls back to `dorkvault_light.qss` if needed.
- `dorkvault.utils.resource_loader.resolve_icon_path()` resolves an icon path and can fall back to `app_icon.svg`.
- `dorkvault.utils.resource_loader.load_icon()` returns a `QIcon` safely, returning an empty icon if no asset is available.

## Icon Handling

- The running Qt application prefers `app_icon.ico` from the bundled assets directory and falls back to `app_icon.svg`.
- The Windows executable icon is assigned separately through PyInstaller using `app_icon.ico`.
- Keeping both formats avoids coupling the Qt runtime icon path to the Windows EXE resource format.

## PyInstaller Layout

The current Windows build script already packages assets and data into the expected bundle structure:

```powershell
--add-data "src/dorkvault/data;dorkvault/data"
--add-data "src/dorkvault/assets;dorkvault/assets"
```

That layout is important because the runtime helpers expect bundled resources to appear under a top-level `dorkvault` folder inside the temporary PyInstaller extraction directory.

## Fallback Behavior

- Missing requested themes fall back to the default bundled theme.
- Missing requested icons can fall back to `app_icon.svg`.
- If no fallback icon exists, the loader returns an empty `QIcon` instead of crashing the application.

## Cross-Platform Notes

- All path handling uses `pathlib.Path`.
- User data resolution prefers `%APPDATA%` on Windows and falls back to a hidden home-directory folder on other platforms.
- Bundled-resource resolution does not rely on hardcoded Windows separators.
