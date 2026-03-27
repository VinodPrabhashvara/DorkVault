# Technique Pack Maintenance

This note explains how the bundled DorkVault catalog is built, what is intentionally excluded, how deduplication works, and how to maintain the packs safely as they grow.

## Pack Layout

The bundled catalog is split into these maintained pack files under `src/dorkvault/data/techniques`:

- `google_dorks.json`
- `github_queries.json`
- `wayback_queries.json`
- `shodan_queries.json`
- `censys_queries.json`
- `ct_logs.json`
- `api_discovery.json`
- `exposed_files.json`
- `cms_queries.json`
- `cloud_storage.json`

Each pack has one stable category, one engine, a shared top-level description, and a sorted technique list.

## Build Workflow

Use the maintained builder instead of editing hundreds of entries by hand:

```powershell
python scripts\build_catalogs.py ".\INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt" src\dorkvault\data\techniques --report docs\reports\catalog_build_report.md
```

The builder combines two inputs:

- a raw semi-structured source collection parsed by `TechniqueCollectionImporter`
- curated generated packs from `TechniqueCatalogBuilder` for providers and query families the raw source does not cover well

The build pipeline then:

1. parses grouped sections and subsections from the raw text source
2. converts safe entries into structured draft records
3. generates stable pack metadata, human-readable names, tags, variables, references, and examples
4. normalizes templates and names before deduplication
5. removes exact duplicates, normalized duplicates, same-category name collisions, and selected near-duplicates
6. writes the final pack JSON files and a markdown build report

## What Gets Excluded

The bundled catalog is intentionally limited to authorized, target-scoped recon. The importer excludes entries that target:

- passwords
- tokens
- API keys
- private keys
- personal data and resumes
- payment-card data
- credential dumps
- secrets in public documents
- social-engineering-oriented harvesting
- third-party paste or collaboration content likely to contain sensitive material
- repository internals and obviously sensitive configuration artifacts

This keeps the built-in catalog focused on:

- target-scoped recon
- public asset discovery
- admin surface discovery
- documentation discovery
- API discovery
- subdomain discovery
- CT log lookups
- Wayback lookups
- cloud asset discovery
- CMS discovery
- exposed file and backup discovery in a general authorized-recon sense

## Deduplication Rules

Deduplication is aggressive, but it is meant to stay predictable and reviewable.

The builder removes:

- exact duplicate query templates
- duplicates after template normalization
- duplicate names inside the same category
- selected near-duplicates when the normalized intent and normalized name both match

Template normalization currently:

- trims surrounding whitespace
- converts smart quotes to plain quotes
- collapses repeated internal whitespace
- normalizes spacing around `:`
- compares case-insensitively for duplicate signatures

The validator also checks for:

- unique technique ids
- required fields
- valid bundled categories
- valid bundled engines
- malformed placeholders
- duplicate exact templates
- duplicate normalized templates
- duplicate normalized names inside the same category
- empty pack descriptions
- examples that do not match the query rendered from variable examples
- pack and category statistics

## Validation Commands

Run validation before packaging:

```powershell
python scripts\validate_techniques.py
pytest tests/test_bundled_catalogs.py tests/test_technique_catalog_builder.py tests/test_technique_catalog_validator.py
```

## Scale Notes

The UI does not need a special alternate layout for the larger bundled catalog. Search and filtering remain simple and responsive because:

- technique search text is precomputed and cached in the `Technique` model
- filtering stays linear and category-aware
- the JSON loader validates once at startup and produces in-memory technique objects

If the bundled catalog keeps growing substantially beyond the current size, prefer improving the build and validation pipeline before adding UI complexity.

## Maintenance Checklist

- Add new entries through the builder pipeline whenever possible.
- Keep names human-readable and consistent with the pack’s engine and category.
- Reuse the shared variables `domain`, `company`, `keyword`, and `org`.
- Write descriptions that explain analyst value, not just query syntax.
- Keep tags focused and searchable.
- Run the builder, validator, and tests before shipping updated packs.
- Review the generated markdown report for unusual duplicate spikes or pack-count drops.

## What DorkVault Cannot Do

- DorkVault is a local query organizer and launcher.
- It does not perform active scanning or exploitation.
- It does not verify findings automatically.
- It does not guarantee search engine results.
- It does not bypass authentication.
- It does not collect secrets automatically.
- It does not ensure legality or authorization for the user.
- It depends on external engines such as Google, GitHub, Wayback, Shodan, and Censys.
- Techniques can become outdated if the packs are not maintained and rebuilt.
