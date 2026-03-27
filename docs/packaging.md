# DorkVault Packaging

This document covers the current packaging approach for DorkVault and the assumptions baked into the project structure.

## Packaging Target

The primary packaging target is a Windows desktop executable built with PyInstaller.

## Current Build Script

Use the existing PowerShell helper:

```powershell
.\scripts\build_exe.ps1
```

Clean old artifacts first if needed:

```powershell
.\scripts\build_exe.ps1 -Clean
```

The packaging flow is centered around two files:

- [DorkVault.spec](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/DorkVault.spec)
- [build_exe.ps1](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/scripts/build_exe.ps1)

The PowerShell script is meant to be reproducible from a clean workstation state. By default it will:

1. create `.venv` if it does not exist
2. upgrade `pip`
3. install dependencies from `requirements.txt`
4. install the project with `pip install -e .`
5. run `pytest`
6. call PyInstaller with the project spec file

Optional flags:

```powershell
.\scripts\build_exe.ps1 -SkipInstall
.\scripts\build_exe.ps1 -SkipTests
```

## Spec File Behavior

The spec file builds a windowed Windows application and bundles:

- `src/dorkvault/data` into `dorkvault/data`
- `src/dorkvault/assets` into `dorkvault/assets`
- the Windows executable icon from `src/dorkvault/assets/icons/app_icon.ico`

The EXE is intentionally built in windowed mode:

- `console=False`
- application name `DorkVault`
- native `.ico` icon assigned to the executable

## Build Inputs

The packaged application depends on these bundled resources:

- JSON technique catalogs
- QSS theme files
- icon assets

There are two icon forms in the project:

- `app_icon.ico` as the preferred runtime Qt icon on Windows and the executable resource
- `app_icon.svg` as the runtime fallback source

The runtime path helpers expect PyInstaller to package them under:

```text
dorkvault/data
dorkvault/assets
```

inside the extracted runtime bundle.

## Runtime Path Strategy

DorkVault uses runtime-aware path helpers so the same code can resolve assets in both:

- development mode
- packaged mode through `sys._MEIPASS`

This keeps UI asset loading and bundled data loading out of the packaging script itself and inside shared application code.

## User-Writable Files

The following files are intentionally not written into the install or bundle directory:

- `settings.json`
- `favorites.json`
- `recents.json`
- `custom_queries.json`
- `dorkvault.log`

These live in the user data directory, which is important because PyInstaller bundles are not appropriate places for mutable runtime state.

## Recommended Packaging Workflow

1. Create and activate `.venv`
2. Run `.\scripts\build_exe.ps1 -Clean`
3. Launch the built app from `dist\DorkVault`
4. Verify:
   asset loading
   bundled technique loading
   user settings persistence
   browser launch behavior
   custom technique creation

## Common Packaging Checks

Before shipping a build, confirm:

- the app starts without missing-theme or missing-icon issues
- techniques load from bundled JSON files
- the light theme applies correctly
- the EXE icon is present in Windows Explorer and the taskbar
- writable user data is created outside the bundle
- logs are written to the user data directory

## Notes For Future Refinement

- add version metadata to the executable
- add a custom icon resource to the final EXE if needed
- consider a `.spec` file if packaging options become more complex
- consider a smoke-test checklist for packaged builds

## Related Docs

- [assets_resolution.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/assets_resolution.md)
- [architecture.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/architecture.md)
