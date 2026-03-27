from __future__ import annotations

from pathlib import Path

from dorkvault.services.technique_catalog_builder import TechniqueCatalogBuilder
from dorkvault.services.technique_catalog_specs import PACK_SPECS
from dorkvault.services.technique_catalog_validator import TechniqueCatalogValidator


def test_builder_creates_large_valid_catalog_from_raw_source(tmp_path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_file = project_root / "INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt"
    output_dir = tmp_path / "catalog"
    report_path = tmp_path / "catalog_build_report.md"

    report = TechniqueCatalogBuilder().build(
        source_file,
        output_dir,
        report_path=report_path,
    )

    assert report.final_count >= 1000
    assert report.generated_count >= 900
    assert len(report.imported_by_file) == len(PACK_SPECS)
    assert report_path.exists()
    assert "Duplicate Removal Summary" in report_path.read_text(encoding="utf-8")

    validation_report = TechniqueCatalogValidator(output_dir).validate()
    assert validation_report.is_valid
    assert validation_report.technique_count == report.final_count
