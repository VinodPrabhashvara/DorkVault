<<<<<<< HEAD
# DorkVault

DorkVault is a local PySide6 desktop application for organizing, filtering, and launching search-based recon techniques used during authorized security research. The project is intentionally data-driven: techniques are loaded from JSON catalogs instead of hardcoded UI buttons, which keeps the application maintainable as the dataset grows.

The current project already includes a working desktop shell, technique loading and validation, query rendering, favorites, recents, local settings, export support, browser integration, custom techniques, light and dark professional themes, and a growing pytest suite.

## Project Overview

DorkVault is designed around a few practical goals:

- keep the UI simple, desktop-friendly, and scalable
- separate UI widgets from data loading, persistence, and business logic
- store user state locally without requiring a backend
- support future growth to hundreds of techniques without rewriting the interface
- stay packaging-friendly for Windows EXE distribution with PyInstaller

## Features

Current implemented capabilities include:

- data-driven technique catalogs loaded from JSON files
- 1000+ bundled safe techniques across Google, GitHub, Wayback, Shodan, Censys, CT logs, cloud storage, CMS, API discovery, and exposed-file packs
- schema validation for techniques and query variables
- search and category filtering across the catalog
- splitter-based desktop layout with sidebar, top bar, technique list, and detail panel
- rendered query preview based on the current target input
- browser launch support for Google, GitHub, Wayback, Shodan, and Censys
- favorites and recent history persistence in local JSON files
- local settings for theme, browser behavior, recent limit, and compact list mode
- custom technique creation, editing, and deletion for user-owned entries
- export support for rendered queries and technique collections
- light and dark QSS themes with runtime-safe asset loading for development and packaged builds
- pytest coverage for the core data and service layers

## Screenshots

Screenshots can be added here as the UI evolves.

- `docs/screenshots/main_window.png`
- `docs/screenshots/technique_detail.png`
- `docs/screenshots/settings_dialog.png`

## Setup

### Windows PowerShell

1. Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

2. Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
pip install -e .
```

## Run

Run the application directly:

```powershell
python -m dorkvault
```

Or use the development helper script:

```powershell
.\scripts\run_dev.ps1
```

The development script will create `.venv` if needed, install dependencies unless `-SkipInstall` is used, and launch the app with `src` on `PYTHONPATH`.

## Test

Run the full test suite:

```powershell
pytest
```

Run a focused subset while working on one area:

```powershell
pytest tests/test_query_renderer.py tests/test_technique_loader.py
```

Validate the bundled technique packs before committing dataset changes:

```powershell
python scripts\validate_techniques.py
```

Import a large text collection into safe structured technique packs:

```powershell
python scripts\import_techniques.py "C:\path\to\collection.txt" src\dorkvault\data\techniques --report docs\reports\import_report.md
```

Build the full bundled catalog from the maintained raw source plus curated generators:

```powershell
python scripts\build_catalogs.py ".\INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt" src\dorkvault\data\techniques --report docs\reports\catalog_build_report.md
```

The catalog build pipeline:

- imports only safe target-scoped recon entries from the raw source
- excludes secrets, credentials, PII, payment data, social-engineering-oriented harvesting, and other inappropriate built-in content
- normalizes names, categories, tags, templates, and examples
- removes exact duplicates, normalized duplicates, and same-category name collisions
- emits a markdown report with final pack counts and duplicate-removal reasons

The current suite focuses on:

- technique schema validation
- JSON loading and repository behavior
- query rendering
- filtering
- favorites persistence
- recent history persistence
- settings persistence
- browser URL generation
- export services

## Packaging

Windows packaging is prepared through PyInstaller.

Build the application:

```powershell
.\scripts\build_exe.ps1
```

Clean old build artifacts first:

```powershell
.\scripts\build_exe.ps1 -Clean
```

The packaging setup now uses:

- [DorkVault.spec](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/DorkVault.spec) for the PyInstaller definition
- [build_exe.ps1](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/scripts/build_exe.ps1) for a reproducible Windows build flow

The build script can bootstrap a clean environment by:

- creating `.venv` if it does not exist
- installing dependencies
- installing the project in editable mode
- running `pytest` before packaging
- building a windowed EXE bundle with the app icon, assets, themes, and technique JSON files

Useful options:

```powershell
.\scripts\build_exe.ps1 -SkipInstall
.\scripts\build_exe.ps1 -SkipTests
```

Bundled runtime resources include:

- `src/dorkvault/data` as bundled runtime data
- `src/dorkvault/assets` as bundled runtime assets

See [packaging.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/packaging.md) for the packaging notes and expected bundle behavior.

## What DorkVault Cannot Do

- DorkVault is a local query organizer and launcher. It does not perform active scanning.
- It does not verify findings automatically or guarantee that external search engines will return results.
- It does not bypass authentication, exploit systems, or collect secrets automatically.
- It does not ensure the user is authorized or acting legally.
- It depends on external engines such as Google, GitHub, Wayback, Shodan, and Censys.
- Bundled techniques can become outdated if the packs are not maintained and rebuilt.

## Project Structure

```text
DorkVault/
|-- docs/
|-- scripts/
|-- src/
|   `-- dorkvault/
|       |-- assets/      # Icons, themes, bundled UI assets
|       |-- core/        # Dataclasses, constants, domain exceptions
|       |-- data/        # Bundled JSON technique catalogs
|       |-- services/    # Loading, rendering, persistence, browser/export logic
|       |-- ui/          # Application bootstrap and top-level windows/dialogs
|       |-- utils/       # Paths, logging, and resource helpers
|       |-- widgets/     # Reusable PySide6 widgets
|       |-- __init__.py
|       |-- __main__.py
|       `-- main.py
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

## Documentation

- [architecture.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/architecture.md)
- [ui_plan.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/ui_plan.md)
- [packaging.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/packaging.md)
- [data_model.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/data_model.md)
- [technique_schema.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/technique_schema.md)
- [data-format.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/data-format.md)
- [technique_packs.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/technique_packs.md)
- [assets_resolution.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/assets_resolution.md)
- [insane_pk_import_report.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/reports/insane_pk_import_report.md)
- [catalog_build_report.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/reports/catalog_build_report.md)
=======
<h1 align="center">DorkVault</h1>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=2563EB&center=true&vCenter=true&width=850&lines=Desktop+Recon+Query+Launcher;Fast+Search+%E2%80%A2+Filter+%E2%80%A2+Preview;Windows+and+Linux+Releases" alt="Typing SVG" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Windows-Supported-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux-Supported-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/UI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" />
  <img src="https://img.shields.io/badge/Source-Available-111827?style=for-the-badge" />
</p>

<p align="center">
  <a href="../../releases/latest"><img src="https://img.shields.io/badge/Download-Latest_Release-2563EB?style=for-the-badge" alt="Download Latest Release" /></a>
  <a href="../../releases"><img src="https://img.shields.io/badge/View-All_Releases-0F172A?style=for-the-badge" alt="View All Releases" /></a>
</p>

---

## Overview

**DorkVault** is a desktop application for organizing, filtering, previewing, and launching search-based reconnaissance techniques from a clean local interface.

It is built for fast workflow, structured technique catalogs, rendered query previews, and simple desktop usability.

## Features

- 1000+ structured techniques
- Fast search and category filtering
- Rendered query preview
- Light and dark themes
- Favorites, recents, and custom local techniques
- Windows and Linux builds

## Quick Start

1. Launch **DorkVault**
2. Enter a target such as `example.com`
3. Search or filter techniques
4. Select a technique
5. Copy the rendered query or open it in your browser

## Releases

- [Latest Release](../../releases/latest)
- [All Releases](../../releases)

## Notes

- For most techniques, use a **domain** like `example.com`, not a full URL
- Results depend on third-party search engines and public indexing
- Use only for authorized security research and permitted assessments

## License

See the [LICENSE](LICENSE) file for details.
>>>>>>> 7feb2e5449bafaaae0a9fb02ebce5e34d1e3682c
