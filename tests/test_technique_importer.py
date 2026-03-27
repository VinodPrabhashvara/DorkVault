from __future__ import annotations

import json

from dorkvault.services.technique_importer import TechniqueCollectionImporter


def test_importer_generates_safe_grouped_packs_and_report(tmp_path) -> None:
    source_file = tmp_path / "collection.txt"
    source_file.write_text(
        "\n".join(
            [
                "[1] FILE & DOCUMENT DISCOVERY",
                'filetype:pdf "internal use only"',
                'filetype:env "DB_PASSWORD"',
                "",
                "[2] LOGIN & ADMIN PANELS",
                "inurl:/admin/login.php",
                "",
                "[12] CMS SPECIFIC DORKS",
                "--- WordPress ---",
                'inurl:"/wp-content/uploads/"',
                'inurl:"/wp-json/wp/v2/users"',
                "",
                "[15] BUG BOUNTY FOCUSED DORKS",
                "site:example.com inurl:api",
                "site:example.com inurl:api",
                "site:example.com filetype:env",
                "",
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    report_path = tmp_path / "import_report.md"

    importer = TechniqueCollectionImporter()
    report = importer.import_file(source_file, output_dir, report_path=report_path)

    assert report.imported_by_file == {
        "api_discovery.json": 1,
        "cms_queries.json": 1,
        "exposed_files.json": 1,
        "google_dorks.json": 1,
    }
    assert len(report.exclusions) == 4

    google_payload = json.loads((output_dir / "google_dorks.json").read_text(encoding="utf-8"))
    exposed_payload = json.loads((output_dir / "exposed_files.json").read_text(encoding="utf-8"))
    api_payload = json.loads((output_dir / "api_discovery.json").read_text(encoding="utf-8"))
    cms_payload = json.loads((output_dir / "cms_queries.json").read_text(encoding="utf-8"))

    assert google_payload["techniques"][0]["query_template"] == "site:{domain} inurl:/admin/login.php"
    assert exposed_payload["techniques"][0]["query_template"] == 'site:{domain} filetype:pdf "internal use only"'
    assert api_payload["techniques"][0]["query_template"] == "site:{domain} inurl:api"
    assert cms_payload["techniques"][0]["query_template"] == 'site:{domain} inurl:"/wp-content/uploads/"'

    report_text = report_path.read_text(encoding="utf-8")
    assert "DB_PASSWORD" in report_text
    assert "wp-json/wp/v2/users" in report_text
    assert "duplicate query template" in report_text.lower()
