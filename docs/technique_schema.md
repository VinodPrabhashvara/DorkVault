# DorkVault Technique Schema

This document defines the JSON structure for individual techniques used by DorkVault. The schema is designed to scale to a large catalog while remaining easy to validate, search, and extend.

## Design Goals

- Keep each technique self-describing and portable.
- Support variable-driven query rendering instead of hardcoded UI logic.
- Preserve room for future metadata such as severity, authorship, deprecation flags, or export tags.
- Stay compatible with grouped category files so one JSON file can contain many techniques.

## Required Technique Fields

Each technique record must provide these fields:

- `id`
  Stable unique identifier such as `github-org-secrets`.
- `name`
  Human-readable label shown in the UI.
- `category`
  Category label such as `GitHub Search` or `Shodan`.
- `engine`
  Search engine or provider name such as `Google`, `GitHub`, `Shodan`, or `Censys`.
- `description`
  Clear explanation of what the technique is meant to find.
- `query_template`
  Query string with named placeholders like `{domain}`, `{company}`, `{keyword}`, or `{org}`.
- `variables`
  Array describing the placeholders used by `query_template`.
- `tags`
  Array of search and organization tags.
- `example`
  Rendered example query for the UI and documentation.
- `safe_mode`
  Boolean flag indicating whether the technique is safe for default display or launching.
- `reference`
  URL or reference string describing the syntax, provider, or supporting documentation.

## Variable Objects

Each entry in `variables` can be either:

- a string shorthand such as `"target"`
- an object with explicit metadata

Variable object fields:

- `name`
  Required. Must use letters, numbers, or underscores.
- `description`
  Optional help text for the UI.
- `required`
  Optional boolean. Defaults to `true`.
- `default`
  Optional default value used when rendering a query.
- `example`
  Optional example value for previews or docs.

## Technique Example

```json
{
  "id": "github-org-secrets",
  "name": "GitHub Org Secrets Hunt",
  "category": "GitHub Search",
  "engine": "GitHub",
  "description": "Search public code for references to a target organization and secret keywords.",
  "query_template": "\"{org}\" (token OR secret OR password)",
  "variables": [
    {
      "name": "org",
      "description": "Organization or company name.",
      "required": true,
      "example": "example-corp"
    }
  ],
  "tags": ["github", "secrets", "osint"],
  "example": "\"example-corp\" (token OR secret OR password)",
  "safe_mode": true,
  "reference": "https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax"
}
```

## Grouped Category File Format

DorkVault stores many techniques per file. Category files wrap technique records like this:

```json
{
  "category_id": "github_search",
  "category_name": "GitHub Search",
  "description": "GitHub code, issue, and repository search techniques.",
  "display_order": 20,
  "techniques": [
    {
      "id": "github-org-secrets",
      "name": "GitHub Org Secrets Hunt",
      "category": "GitHub Search",
      "engine": "GitHub",
      "description": "Search public code for references to a target organization and secret keywords.",
      "query_template": "\"{org}\" (token OR secret OR password)",
      "variables": ["org"],
      "tags": ["github", "secrets", "osint"],
      "example": "\"example-corp\" (token OR secret OR password)",
      "safe_mode": true,
      "reference": "https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax"
    }
  ]
}
```

Category files can also include optional sidebar grouping metadata when the catalog is organized into larger themed pack collections:

- `category_group_id`
- `category_group_name`
- `category_group_description`
- `category_group_display_order`

If those fields are omitted, DorkVault still loads the pack automatically and falls back to the pack's relative directory structure when available.

## Validation Rules

- `id`, `name`, `category`, `engine`, `description`, and `query_template` must be non-empty strings.
- `safe_mode` must be a boolean.
- `variables` must be a list.
- Variable names must be unique within a technique.
- Every placeholder referenced in `query_template` must have a matching variable entry.
- Tags are normalized to lowercase to keep filtering consistent.

## Recommended Placeholder Vocabulary

To keep the dataset predictable at scale, prefer these variable names:

- `domain`
- `company`
- `keyword`
- `org`

Using a smaller shared vocabulary makes rendering, filtering, and future UI improvements easier.

## Large Pack Maintenance

When the built-in catalog grows, treat the files like curated datasets rather than a dump of similar dorks.

- Keep one file per category.
- Use stable IDs and avoid renaming them after release.
- Avoid near-duplicate techniques that differ only by a tiny keyword change.
- Keep descriptions focused on analyst value, not just the raw query.
- Run `python scripts\validate_techniques.py` before committing changes.

For day-to-day maintenance guidance, see `docs/data-format.md`.

## Compatibility Notes

The current repository loader also accepts legacy starter records that still use fields such as `provider`, `target_hint`, `notes`, and `launch_url`. Those are normalized into the new schema at load time so the project can transition without breaking the scaffold.
