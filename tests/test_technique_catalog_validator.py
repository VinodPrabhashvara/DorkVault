from __future__ import annotations

import json
from pathlib import Path

from dorkvault.services.technique_catalog_specs import PACK_SPECS
from dorkvault.services.technique_catalog_validator import TechniqueCatalogValidator


def _write_category_file(tmp_path, file_name: str, category_name: str, techniques: list[dict]) -> None:
    spec = PACK_SPECS.get(file_name.removesuffix(".json"))
    payload = {
        "category_id": file_name.removesuffix(".json"),
        "category_name": category_name,
        "description": f"{category_name} techniques",
        "display_order": spec.display_order if spec is not None else 10,
        "techniques": techniques,
    }
    target_path = tmp_path / file_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _technique_record(
    *,
    technique_id: str,
    name: str,
    category: str,
    engine: str,
    query_template: str = "\"{domain}\"",
    example: str | None = None,
) -> dict:
    return {
        "id": technique_id,
        "name": name,
        "category": category,
        "engine": engine,
        "description": f"{name} description",
        "query_template": query_template,
        "variables": ["domain"],
        "tags": [engine.lower(), "test", "catalog"],
        "example": example or query_template.format(domain="example.com"),
        "safe_mode": True,
        "reference": f"https://example.com/{technique_id}",
        "launch_url": "https://example.com/search?q={query}",
    }


def test_validator_accepts_bundled_catalogs(bundled_techniques_dir) -> None:
    report = TechniqueCatalogValidator(bundled_techniques_dir).validate()

    assert report.is_valid
    assert report.files_scanned == len(list(Path(bundled_techniques_dir).rglob("*.json")))
    assert report.technique_count >= 1000
    assert report.pack_statistics
    assert report.category_statistics


def test_validator_collects_duplicate_ids_empty_fields_and_malformed_templates(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "google_dorks.json",
        "Google Dorks",
        [
            _technique_record(
                technique_id="shared-id",
                name="Google Valid",
                category="Google Dorks",
                engine="Google",
            ),
            {
                "id": "missing-name",
                "name": "",
                "category": "Google Dorks",
                "engine": "Google",
                "description": "Name is empty",
                "query_template": "\"{domain}\"",
                "variables": ["domain"],
                "tags": ["google", "test", "invalid"],
                "example": "\"example.com\"",
                "safe_mode": True,
                "reference": "https://example.com/missing-name",
            },
        ],
    )
    _write_category_file(
        tmp_path,
        "github_queries.json",
        "GitHub Search",
        [
            _technique_record(
                technique_id="shared-id",
                name="Duplicate Id",
                category="GitHub Search",
                engine="GitHub",
            ),
            _technique_record(
                technique_id="malformed-template",
                name="Malformed Template",
                category="GitHub Search",
                engine="GitHub",
                query_template="site:{domain",
                example="site:example.com",
            ),
        ],
    )

    report = TechniqueCatalogValidator(tmp_path).validate()

    assert not report.is_valid
    assert len(report.issues) == 3
    issue_text = "\n".join(issue.display_text() for issue in report.issues)
    assert "missing-name" in issue_text
    assert "shared-id" in issue_text
    assert "Malformed" in issue_text or "template" in issue_text.lower()


def test_validator_collects_duplicate_query_templates(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "google_dorks.json",
        "Google Dorks",
        [
            _technique_record(
                technique_id="google-login",
                name="Google Login",
                category="Google Dorks",
                engine="Google",
                query_template="site:{domain} inurl:login",
                example="site:example.com inurl:login",
            )
        ],
    )
    _write_category_file(
        tmp_path,
        "api_discovery.json",
        "API Discovery",
        [
            _technique_record(
                technique_id="custom-login",
                name="Custom Login",
                category="API Discovery",
                engine="Google",
                query_template="site:{domain} inurl:login",
                example="site:example.com inurl:login",
            )
        ],
    )

    report = TechniqueCatalogValidator(tmp_path).validate()

    assert not report.is_valid
    assert len(report.issues) == 1
    assert "Duplicate technique query" in report.issues[0].message


def test_validator_collects_normalized_duplicates_duplicate_names_and_invalid_examples(tmp_path) -> None:
    _write_category_file(
        tmp_path,
        "google_dorks.json",
        "Google Dorks",
        [
            _technique_record(
                technique_id="google-login",
                name="Login Search",
                category="Google Dorks",
                engine="Google",
                query_template="site:{domain} inurl:login",
                example="site:example.com inurl:login",
            ),
            _technique_record(
                technique_id="google-login-duplicate",
                name="  Login   Search  ",
                category="Google Dorks",
                engine="Google",
                query_template="site:{domain}   inurl:login",
                example="site:example.com   inurl:login",
            ),
            _technique_record(
                technique_id="google-docs-invalid-example",
                name="Documentation Search",
                category="Google Dorks",
                engine="Google",
                query_template="site:{domain} inurl:docs",
                example="site:example.com inurl:admin",
            ),
            _technique_record(
                technique_id="google-login-name-duplicate",
                name="Login Search",
                category="Google Dorks",
                engine="Google",
                query_template="site:{domain} intitle:login",
                example="site:example.com intitle:login",
            ),
        ],
    )

    report = TechniqueCatalogValidator(tmp_path).validate()

    assert not report.is_valid
    issue_text = "\n".join(issue.display_text() for issue in report.issues)
    assert "Normalized duplicate technique query" in issue_text
    assert "Duplicate technique name already defined in the same category" in issue_text
    assert "Technique example does not match" in issue_text


def test_validator_scans_nested_pack_directories(tmp_path) -> None:
    nested_dir = tmp_path / "google" / "discovery"
    _write_category_file(
        nested_dir,
        "google_dorks.json",
        "Google Dorks",
        [
            _technique_record(
                technique_id="google-login",
                name="Google Login",
                category="Google Dorks",
                engine="Google",
            )
        ],
    )

    report = TechniqueCatalogValidator(tmp_path).validate()

    assert report.is_valid
    assert report.files_scanned == 1
    assert report.technique_count == 1
