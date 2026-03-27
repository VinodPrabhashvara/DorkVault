"""Validate bundled technique catalogs before they are shipped."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from dorkvault.core.models import Technique
from dorkvault.services.technique_catalog_normalization import (
    normalize_name,
    normalize_template,
    normalized_template_signature,
)
from dorkvault.services.technique_catalog_specs import CATEGORY_NAMES, ENGINE_NAMES, PACK_SPECS, VARIABLE_LIBRARY
from dorkvault.utils.paths import get_data_dir


@dataclass(slots=True, frozen=True)
class TechniqueCatalogValidationIssue:
    """A single validation issue found while reviewing technique catalogs."""

    source_file: str
    message: str
    entry_index: int | None = None
    technique_id: str = ""

    def display_text(self) -> str:
        """Return a readable issue string for logs and CLI output."""
        location = self.source_file
        if self.entry_index is not None:
            location += f" entry #{self.entry_index}"
        if self.technique_id:
            location += f" ({self.technique_id})"
        return f"{location}: {self.message}"


@dataclass(slots=True)
class TechniqueCatalogValidationReport:
    """Aggregated validation results for one technique catalog directory."""

    files_scanned: int = 0
    technique_count: int = 0
    issues: list[TechniqueCatalogValidationIssue] = field(default_factory=list)
    pack_statistics: dict[str, int] = field(default_factory=dict)
    category_statistics: dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when the directory has no validation issues."""
        return not self.issues


class TechniqueCatalogValidator:
    """Validate large grouped technique packs without stopping at the first error."""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.data_dir = data_dir or (get_data_dir() / "techniques")
        self.logger = logger or logging.getLogger(__name__)

    def validate(self) -> TechniqueCatalogValidationReport:
        """Validate all JSON files in the configured technique directory."""
        report = TechniqueCatalogValidationReport()

        if not self.data_dir.exists():
            report.issues.append(
                TechniqueCatalogValidationIssue(
                    source_file=str(self.data_dir),
                    message="Technique data directory was not found.",
                )
            )
            return report

        json_files = sorted(
            self.data_dir.rglob("*.json"),
            key=lambda item: item.relative_to(self.data_dir).as_posix().lower(),
        )
        report.files_scanned = len(json_files)
        if not json_files:
            report.issues.append(
                TechniqueCatalogValidationIssue(
                    source_file=str(self.data_dir),
                    message="No technique JSON files were found.",
                )
            )
            return report

        technique_sources: dict[str, str] = {}
        exact_templates: dict[tuple[str, str], tuple[str, str]] = {}
        normalized_templates: dict[tuple[str, str], tuple[str, str]] = {}
        names_by_category: dict[tuple[str, str], tuple[str, str]] = {}

        for json_path in json_files:
            source_file = json_path.relative_to(self.data_dir).as_posix()
            issues_before = len(report.issues)
            payload = self._read_json(json_path, report, source_file=source_file)
            if payload is None:
                continue

            file_name = json_path.name
            spec = PACK_SPECS.get(file_name.removesuffix(".json"))
            category_name = str(payload.get("category_name", "")).strip()
            category_id = str(payload.get("category_id", "")).strip()
            description = str(payload.get("description", "")).strip()
            display_order = payload.get("display_order")
            raw_techniques = payload.get("techniques", [])

            if not category_id or not category_name:
                report.issues.append(
                    TechniqueCatalogValidationIssue(
                        source_file=source_file,
                        message="Category metadata must include non-empty category_id and category_name.",
                    )
                )
                continue

            if category_name not in CATEGORY_NAMES:
                report.issues.append(
                    TechniqueCatalogValidationIssue(
                        source_file=source_file,
                        message=f"Unknown category_name '{category_name}'.",
                    )
                )

            if spec is not None:
                if category_id != spec.category_id:
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            message=(
                                f"category_id must match the bundled pack definition '{spec.category_id}'."
                            ),
                        )
                    )
                if category_name != spec.category_name:
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            message=(
                                f"category_name must match the bundled pack definition '{spec.category_name}'."
                            ),
                        )
                    )
                if display_order != spec.display_order:
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            message=(
                                f"display_order must match the bundled pack definition '{spec.display_order}'."
                            ),
                        )
                    )

            if not description:
                report.issues.append(
                    TechniqueCatalogValidationIssue(
                        source_file=source_file,
                        message="Pack description must be a non-empty string.",
                    )
                )

            if not isinstance(raw_techniques, list):
                report.issues.append(
                    TechniqueCatalogValidationIssue(
                        source_file=source_file,
                        message="Top-level techniques field must be a list.",
                    )
                )
                continue

            valid_techniques_in_file = 0
            for index, raw_item in enumerate(raw_techniques, start=1):
                if not isinstance(raw_item, dict):
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            entry_index=index,
                            message="Technique entry must be a JSON object.",
                        )
                    )
                    continue

                try:
                    technique = Technique.from_dict(
                        raw_item,
                        default_category=category_name,
                        source_file=source_file,
                    )
                except ValueError as exc:
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            entry_index=index,
                            technique_id=str(raw_item.get("id", "")).strip(),
                            message=str(exc),
                        )
                    )
                    continue

                issue_message = self._validate_technique_record(
                    technique=technique,
                    source_file=source_file,
                    category_name=category_name,
                    spec=spec,
                    technique_sources=technique_sources,
                    exact_templates=exact_templates,
                    normalized_templates=normalized_templates,
                    names_by_category=names_by_category,
                )
                if issue_message is not None:
                    report.issues.append(
                        TechniqueCatalogValidationIssue(
                            source_file=source_file,
                            entry_index=index,
                            technique_id=technique.id,
                            message=issue_message,
                        )
                    )
                    continue

                technique_sources[technique.id] = source_file
                exact_templates[
                    (technique.engine.strip().lower(), technique.query_template.strip())
                ] = (source_file, technique.id)
                normalized_templates[
                    normalized_template_signature(technique.engine, technique.query_template)
                ] = (source_file, technique.id)
                names_by_category[
                    (technique.category, normalize_name(technique.name))
                ] = (source_file, technique.id)
                valid_techniques_in_file += 1
                report.technique_count += 1
                report.category_statistics[technique.category] = (
                    report.category_statistics.get(technique.category, 0) + 1
                )

            report.pack_statistics[source_file] = valid_techniques_in_file
            if len(report.issues) == issues_before:
                self.logger.info(
                    "Validated technique file successfully.",
                    extra={
                        "event": "technique_catalog_validated",
                        "source_file": source_file,
                        "technique_count": valid_techniques_in_file,
                    },
                )

        return report

    def _validate_technique_record(
        self,
        *,
        technique: Technique,
        source_file: str,
        category_name: str,
        spec,
        technique_sources: dict[str, str],
        exact_templates: dict[tuple[str, str], tuple[str, str]],
        normalized_templates: dict[tuple[str, str], tuple[str, str]],
        names_by_category: dict[tuple[str, str], tuple[str, str]],
    ) -> str | None:
        existing_source = technique_sources.get(technique.id)
        if existing_source is not None:
            return f"Duplicate technique id already defined in {existing_source}."

        if technique.category != category_name:
            return (
                "Technique category does not match the file category_name. "
                f"Expected '{category_name}'."
            )

        if technique.category not in CATEGORY_NAMES:
            return f"Technique category '{technique.category}' is not a bundled category."

        if technique.engine not in ENGINE_NAMES:
            return f"Technique engine '{technique.engine}' is not a supported bundled engine."

        if spec is not None and technique.engine != spec.engine:
            return (
                "Technique engine does not match the pack engine. "
                f"Expected '{spec.engine}'."
            )

        exact_signature = (
            technique.engine.strip().lower(),
            technique.query_template.strip(),
        )
        existing_exact = exact_templates.get(exact_signature)
        if existing_exact is not None:
            existing_file, existing_id = existing_exact
            return f"Duplicate technique query already defined in {existing_file} ({existing_id})."

        normalized_signature = normalized_template_signature(
            technique.engine,
            technique.query_template,
        )
        existing_normalized = normalized_templates.get(normalized_signature)
        if existing_normalized is not None:
            existing_file, existing_id = existing_normalized
            return (
                "Normalized duplicate technique query already defined in "
                f"{existing_file} ({existing_id})."
            )

        name_key = (technique.category, normalize_name(technique.name))
        existing_name = names_by_category.get(name_key)
        if existing_name is not None:
            existing_file, existing_id = existing_name
            return (
                "Duplicate technique name already defined in the same category in "
                f"{existing_file} ({existing_id})."
            )

        expected_example = self._expected_example(technique)
        if normalize_template(technique.example) != normalize_template(expected_example):
            return (
                "Technique example does not match the rendered query produced from its variable examples."
            )

        return None

    def _expected_example(self, technique: Technique) -> str:
        values: dict[str, str] = {}
        for variable in technique.variables:
            if variable.example:
                values[variable.name] = variable.example
                continue
            if variable.default:
                values[variable.name] = variable.default
                continue

            spec = VARIABLE_LIBRARY.get(variable.name)
            if spec is not None:
                values[variable.name] = str(spec["example"])
                continue

            fallback = variable.name.replace("_", " ").strip() or "example"
            values[variable.name] = fallback
        return technique.render_query(values)

    def _read_json(
        self,
        json_path: Path,
        report: TechniqueCatalogValidationReport,
        *,
        source_file: str,
    ) -> dict | None:
        try:
            with json_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            report.issues.append(
                TechniqueCatalogValidationIssue(
                    source_file=source_file,
                    message=f"Invalid JSON: {exc}",
                )
            )
            return None
        except OSError as exc:
            report.issues.append(
                TechniqueCatalogValidationIssue(
                    source_file=source_file,
                    message=f"File could not be read: {exc}",
                )
            )
            return None

        if not isinstance(payload, dict):
            report.issues.append(
                TechniqueCatalogValidationIssue(
                    source_file=source_file,
                    message="Top-level JSON payload must be an object.",
                )
            )
            return None
        return payload


def main(argv: list[str] | None = None) -> int:
    """Run the catalog validator as a small CLI utility."""
    parser = argparse.ArgumentParser(
        description="Validate DorkVault technique catalog files."
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        type=Path,
        default=get_data_dir() / "techniques",
        help="Path to the technique JSON directory.",
    )
    args = parser.parse_args(argv)

    validator = TechniqueCatalogValidator(args.data_dir)
    report = validator.validate()

    print(
        f"Scanned {report.files_scanned} file(s) and validated "
        f"{report.technique_count} technique(s)."
    )
    if report.pack_statistics:
        print("Pack statistics:")
        for source_file, count in sorted(report.pack_statistics.items()):
            print(f"- {source_file}: {count}")
    if report.category_statistics:
        print("Category statistics:")
        for category_name, count in sorted(report.category_statistics.items()):
            print(f"- {category_name}: {count}")
    if report.is_valid:
        print("Technique catalogs are valid.")
        return 0

    print(f"Found {len(report.issues)} issue(s):")
    for issue in report.issues:
        print(f"- {issue.display_text()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
