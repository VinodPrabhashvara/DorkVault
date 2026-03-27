# DorkVault Architecture

This document describes the current architectural shape of DorkVault and the boundaries the project is trying to preserve as it grows.

## Goals

- keep techniques data-driven and externalized in JSON
- keep PySide6 UI code separate from business logic and persistence
- make desktop packaging straightforward
- support future expansion without turning the app into a monolith

## High-Level Design

DorkVault is a local desktop application with a layered structure:

1. `core`
   Domain models, constants, and application-specific exceptions.
2. `services`
   Data loading, query rendering, browser integration, filtering, export, settings, favorites, recents, and custom-technique persistence.
3. `ui`
   Application startup, main window coordination, and modal dialogs.
4. `widgets`
   Reusable view components such as the sidebar, top bar, technique list, and detail panel.
5. `utils`
   Cross-cutting helpers for logging, runtime paths, and bundled resource loading.
6. `data` and `assets`
   Bundled JSON catalogs, themes, and icons.

## Runtime Flow

1. `python -m dorkvault` enters [main.py](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/src/dorkvault/main.py).
2. The Qt application is created in [app.py](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/src/dorkvault/ui/app.py).
3. Logging is configured and the selected theme/icon assets are loaded.
4. [main_window.py](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/src/dorkvault/ui/main_window.py) initializes services and widgets.
5. [technique_repository.py](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/src/dorkvault/services/technique_repository.py) loads bundled and user custom techniques.
6. The main window synchronizes sidebar state, top-bar filters, the technique list, and the detail panel through signals and service calls.

## Package Responsibilities

### `src/dorkvault/core`

- `models.py`
  Technique schema, variable schema, settings model, and category model.
- `constants.py`
  Application constants and runtime defaults.
- `exceptions.py`
  Domain-specific exception types used across services and UI.

### `src/dorkvault/services`

- `technique_loader.py`
  Reads and validates technique JSON files.
- `technique_repository.py`
  Merges built-in and custom techniques and exposes query/filter access.
- `query_renderer.py`
  Renders query templates from variable values.
- `technique_filter_service.py`
  Applies category and text filtering.
- `browser_service.py`
  Builds supported engine URLs and opens the browser.
- `launcher_service.py`
  Bridges technique rendering with browser launch behavior.
- `favorites_service.py`
  Local favorites persistence.
- `recent_history_service.py`
  Local recent-history persistence.
- `settings_service.py`
  Local settings persistence and normalization.
- `custom_technique_service.py`
  User custom-technique creation, editing, deletion, and file persistence.
- `export_service.py`
  TXT and JSON export helpers.

### `src/dorkvault/ui`

- `app.py`
  Qt bootstrap and top-level startup safeguards.
- `main_window.py`
  Central coordination layer that wires widgets to services.
- `settings_dialog.py`
  Settings editing dialog.
- `custom_technique_dialog.py`
  Custom-technique creation and editing dialog.

### `src/dorkvault/widgets`

- `sidebar.py`
  Section navigation and category filter UI.
- `target_toolbar.py`
  Target input, search, category quick filter, and action buttons.
- `technique_list.py`
  Scalable list/card view backed by a model and delegate.
- `detail_panel.py`
  Selected-technique details, preview, and actions.

## Data Sources

DorkVault currently uses two data sources:

- bundled technique catalogs under `src/dorkvault/data/techniques`
- user custom techniques under the writable user data directory

This split keeps built-in catalogs read-only while still allowing local extension.

## Local Persistence

User files are stored outside the install directory:

- settings JSON
- favorites JSON
- recents JSON
- custom technique JSON
- rotating log file

On Windows, this resolves under `%APPDATA%\DorkVault`. The same pattern is compatible with packaged builds because writable state is not stored beside the executable.

## Design Decisions

### Data-Driven Catalogs

Techniques are externalized so the application can scale to hundreds of entries without adding or maintaining large blocks of hardcoded UI.

### Thin Widgets, Service-Backed Behavior

Widgets are kept presentation-focused where possible. Logic such as rendering, filtering, export, persistence, and browser launch lives in services so it is easier to test and evolve.

### Simple Local Storage

JSON is used for small local state because it is transparent, easy to inspect during development, and sufficient for the current scope.

### PyInstaller-Friendly Layout

Assets and data are loaded through runtime-aware path helpers so the same code works in development and packaged mode.

## Reliability Notes

The project now includes:

- structured logging with contextual metadata
- domain-specific exceptions for common failure modes
- user-friendly error messages for common issues
- tests that cover the main non-UI layers

## Related Documents

- [ui_plan.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/ui_plan.md)
- [packaging.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/packaging.md)
- [data_model.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/data_model.md)
- [technique_schema.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/technique_schema.md)
