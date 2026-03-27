# DorkVault Data Model

This document summarizes the main application data models and how they are used at runtime.

## Core Models

The core dataclasses live in [models.py](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/src/dorkvault/core/models.py).

## `TechniqueVariable`

Represents a single named placeholder used in a query template.

Fields:

- `name`
- `description`
- `required`
- `default`
- `example`

Purpose:

- defines what user input or default value is needed to render a query
- keeps variable metadata close to the technique definition

## `Technique`

Represents one search or recon technique loaded from JSON.

Key fields:

- `id`
- `name`
- `category`
- `engine`
- `description`
- `query_template`
- `variables`
- `tags`
- `example`
- `safe_mode`
- `reference`
- `launch_url`
- `source_file`

Responsibilities:

- validate required technique fields
- validate variable declarations and placeholder usage
- expose helper methods for rendering and search indexing
- support legacy starter-record normalization where needed

Helpful computed properties:

- `variable_names`
- `required_variables`
- `primary_variable_name`
- `template_variables`

Helpful methods:

- `from_dict()`
- `render_query()`
- `build_query()`
- `build_variables_from_target_input()`
- `build_url()`
- `search_text()`

## `TechniqueCategory`

Represents a category grouping techniques inside the repository.

Fields:

- `id`
- `name`
- `description`
- `display_order`
- `techniques`

Purpose:

- lets the loader and repository organize techniques into sidebar and filter-friendly groupings

## `AppSettings`

Represents persisted local application settings.

Current fields:

- `theme`
- `open_in_browser_behavior`
- `recent_limit`
- `compact_view_enabled`
- `last_target`

Purpose:

- keeps local UI/runtime configuration normalized
- supports safe loading from JSON with defaults

## Data Flow

### Technique Catalogs

1. JSON files are loaded by `TechniqueLoader`
2. Each entry is validated into `Technique` instances
3. `TechniqueRepository` merges built-in and custom techniques
4. The UI consumes the repository output

### Query Rendering

1. A selected `Technique` and variable values are passed to `QueryRenderer`
2. Template placeholders are validated and rendered
3. Browser/export/clipboard actions use the rendered output

### User State

User state is stored in small JSON documents managed by dedicated services:

- favorites
- recents
- settings
- custom techniques

This keeps the data model simple and the persistence responsibilities separated.

## JSON Schema Reference

For the full technique JSON schema, examples, and field-level rules, see:

- [technique_schema.md](/p:/Ethical%20Hacking/Pentesting/CLI%20tools/DorkVault/docs/technique_schema.md)
