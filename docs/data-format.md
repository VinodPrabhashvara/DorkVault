# Technique Data Format

This document is a practical guide for maintaining the built-in technique packs under `src/dorkvault/data/techniques`.

For field-level validation rules, see `docs/technique_schema.md`.

## Pack Layout

Technique packs are discovered automatically from `src/dorkvault/data/techniques` and any nested subdirectories.

Each category usually lives in one JSON file:

- `google_dorks.json`
- `github_queries.json`
- `wayback_queries.json`
- `shodan_queries.json`
- `censys_queries.json`
- `cloud_storage.json`
- `cms_queries.json`
- `exposed_files.json`
- `api_discovery.json`
- `ct_logs.json`

Each file contains:

```json
{
  "category_id": "google_dorks",
  "category_name": "Google Dorks",
  "description": "Search engine queries for discovering indexed content and exposure clues.",
  "display_order": 10,
  "techniques": [
    {
      "id": "google-domain-directory-indexes",
      "name": "Directory Index Discovery",
      "category": "Google Dorks",
      "engine": "Google",
      "description": "Looks for indexed directory listing pages on a target domain.",
      "query_template": "site:{domain} intitle:\"index of\"",
      "variables": [
        {
          "name": "domain",
          "description": "Primary target domain or host name.",
          "required": true,
          "example": "example.com"
        }
      ],
      "tags": ["google", "directory-listing", "files", "exposure", "osint"],
      "example": "site:example.com intitle:\"index of\"",
      "safe_mode": true,
      "reference": "https://support.google.com/websearch/answer/2466433",
      "launch_url": "https://www.google.com/search?q={query}"
    }
  ]
}
```

When a larger catalog is split into themed folders, packs can optionally define:

- `category_group_id`
- `category_group_name`
- `category_group_description`
- `category_group_display_order`

If those fields are not present, DorkVault derives a sidebar group from the pack's relative folder path.

## Maintenance Rules

- Keep techniques grouped by category instead of building one massive JSON file.
- Use stable, descriptive IDs like `github-org-api-surface-search`.
- Prefer one clear recon intent per technique.
- Avoid near-duplicates that only change one keyword or file extension.
- Keep tags specific and useful for filtering. Aim for 4 to 6 tags.
- Use only search and lookup queries. Do not add active scanning or automation steps.
- Keep `category` aligned with the file's `category_name`.
- Prefer the shared placeholder vocabulary: `{domain}`, `{company}`, `{keyword}`, `{org}`.

## Placeholder Conventions

Use placeholders consistently so the UI and renderer stay predictable:

- `{domain}` for hostnames or domains such as `example.com`
- `{company}` for brand or company names such as `Example Corp`
- `{keyword}` for product names, feature names, or free-text terms
- `{org}` for organization names, business units, or GitHub org slugs

Do not invent multiple synonyms for the same concept unless there is a strong reason.

## Validation Workflow

Before committing pack updates, run:

```powershell
python scripts\validate_techniques.py
```

If the project is installed in editable mode, this also works:

```powershell
dorkvault-validate-techniques
```

The validator checks for:

- duplicate technique IDs across files
- empty required fields
- malformed or mismatched variable placeholders
- category mismatches within grouped files

Follow with the test suite:

```powershell
pytest tests/test_bundled_catalogs.py tests/test_technique_catalog_validator.py
```
