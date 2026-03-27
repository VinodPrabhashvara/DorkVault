"""Build the bundled DorkVault technique catalog from safe reusable sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

from dorkvault.services.technique_catalog_normalization import (
    near_duplicate_signature,
    normalize_name,
    normalize_template,
    normalized_template_signature,
)
from dorkvault.services.technique_catalog_specs import PACK_SPECS, VARIABLE_LIBRARY, TechniquePackSpec
from dorkvault.services.technique_importer import TechniqueCollectionImporter, TechniqueImportReport


@dataclass(slots=True, frozen=True)
class TechniqueDraft:
    """Intermediate technique data before IDs and pack metadata are applied."""

    pack_key: str
    name: str
    query_template: str
    description: str
    tags: tuple[str, ...]
    variables: tuple[str, ...]
    source: str
    reference: str = ""
    launch_url: str = ""


@dataclass(slots=True, frozen=True)
class DuplicateRemoval:
    """A draft removed during deduplication."""

    pack_key: str
    name: str
    query_template: str
    reason: str
    kept_name: str
    kept_query_template: str
    source: str


@dataclass(slots=True)
class CatalogBuildReport:
    """Summary of one catalog build."""

    source_file: str
    output_dir: str
    raw_import_report: TechniqueImportReport
    imported_by_file: dict[str, int] = field(default_factory=dict)
    duplicate_removals: list[DuplicateRemoval] = field(default_factory=list)
    generated_count: int = 0

    @property
    def final_count(self) -> int:
        return sum(self.imported_by_file.values())


class TechniqueCatalogBuilder:
    """Generate large safe technique packs from raw and curated sources."""

    def __init__(self, importer: TechniqueCollectionImporter | None = None) -> None:
        self.importer = importer or TechniqueCollectionImporter()

    def build(
        self,
        source_path: Path,
        output_dir: Path,
        *,
        report_path: Path | None = None,
    ) -> CatalogBuildReport:
        raw_drafts, raw_report = self._load_raw_drafts(source_path)
        generated_drafts = self._generated_drafts()
        kept_drafts, duplicate_removals = self._deduplicate_drafts([*raw_drafts, *generated_drafts])

        output_dir.mkdir(parents=True, exist_ok=True)
        imported_by_file: dict[str, int] = {}
        grouped_drafts: dict[str, list[TechniqueDraft]] = defaultdict(list)
        for draft in kept_drafts:
            grouped_drafts[draft.pack_key].append(draft)

        for pack_key, spec in PACK_SPECS.items():
            pack_drafts = grouped_drafts.get(pack_key, [])
            payload = {
                "category_id": spec.category_id,
                "category_name": spec.category_name,
                "description": spec.description,
                "display_order": spec.display_order,
                "techniques": [self._draft_to_payload(spec, draft) for draft in pack_drafts],
            }
            (output_dir / spec.file_name).write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            imported_by_file[spec.file_name] = len(pack_drafts)

        report = CatalogBuildReport(
            source_file=str(source_path),
            output_dir=str(output_dir),
            raw_import_report=raw_report,
            imported_by_file=imported_by_file,
            duplicate_removals=duplicate_removals,
            generated_count=len(generated_drafts),
        )
        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(self.render_report(report), encoding="utf-8")
        return report

    def render_report(self, report: CatalogBuildReport) -> str:
        duplicate_reason_counts = Counter(item.reason for item in report.duplicate_removals)
        raw_exclusion_counts = Counter(item.reason for item in report.raw_import_report.exclusions)
        lines = [
            "# Technique Catalog Build Report",
            "",
            f"- Source: `{report.source_file}`",
            f"- Output directory: `{report.output_dir}`",
            f"- Generated supplemental drafts: `{report.generated_count}`",
            f"- Final bundled techniques: `{report.final_count}`",
            f"- Raw-source exclusions: `{len(report.raw_import_report.exclusions)}`",
            f"- Duplicate removals: `{len(report.duplicate_removals)}`",
            "",
            "## Final Pack Counts",
            "",
        ]

        for file_name, count in sorted(report.imported_by_file.items()):
            lines.append(f"- `{file_name}`: {count} technique(s)")

        lines.extend(["", "## Raw Import Exclusion Summary", ""])
        if raw_exclusion_counts:
            for reason, count in raw_exclusion_counts.most_common():
                lines.append(f"- {count} line(s): {reason}")
        else:
            lines.append("- No raw-source exclusions.")

        lines.extend(["", "## Duplicate Removal Summary", ""])
        if duplicate_reason_counts:
            for reason, count in duplicate_reason_counts.most_common():
                lines.append(f"- {count} removal(s): {reason}")
        else:
            lines.append("- No duplicates were removed.")

        lines.extend(["", "## Sample Duplicate Removals", ""])
        for removal in report.duplicate_removals[:25]:
            lines.append(
                f"- `{removal.name}` [{removal.pack_key}] from `{removal.source}` removed because "
                f"{removal.reason}. Kept `{removal.kept_name}`."
            )
            lines.append(f"  Removed: `{removal.query_template}`")
            lines.append(f"  Kept: `{removal.kept_query_template}`")
        if not report.duplicate_removals:
            lines.append("- No duplicate removals to show.")

        lines.extend(["", "## Sample Raw Exclusions", ""])
        for exclusion in report.raw_import_report.exclusions[:20]:
            subsection = f" / {exclusion.subsection_title}" if exclusion.subsection_title else ""
            lines.append(
                f"- Line {exclusion.line_number} [{exclusion.section_title}{subsection}]: "
                f"`{exclusion.raw_query}`"
            )
            lines.append(f"  Reason: {exclusion.reason}")
        if not report.raw_import_report.exclusions:
            lines.append("- No raw-source exclusions to show.")

        lines.append("")
        return "\n".join(lines)

    def _load_raw_drafts(self, source_path: Path) -> tuple[list[TechniqueDraft], TechniqueImportReport]:
        with TemporaryDirectory(prefix="dorkvault_catalog_build_") as temp_dir:
            raw_report = self.importer.import_file(source_path, Path(temp_dir))
            drafts: list[TechniqueDraft] = []
            for file_name in raw_report.imported_by_file:
                payload = json.loads((Path(temp_dir) / file_name).read_text(encoding="utf-8"))
                pack_key = file_name.removesuffix(".json")
                for technique_payload in payload.get("techniques", []):
                    drafts.append(
                        TechniqueDraft(
                            pack_key=pack_key,
                            name=str(technique_payload["name"]).strip(),
                            query_template=str(technique_payload["query_template"]).strip(),
                            description=str(technique_payload["description"]).strip(),
                            tags=tuple(str(tag).strip().lower() for tag in technique_payload["tags"]),
                            variables=tuple(
                                str(variable["name"]).strip()
                                for variable in technique_payload["variables"]
                            ),
                            source=f"raw:{source_path.name}",
                            reference=str(technique_payload.get("reference", "")).strip(),
                            launch_url=str(technique_payload.get("launch_url", "")).strip(),
                        )
                    )
        return drafts, raw_report

    def _generated_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        drafts.extend(self._generate_google_drafts())
        drafts.extend(self._generate_api_discovery_drafts())
        drafts.extend(self._generate_exposed_file_drafts())
        drafts.extend(self._generate_cms_drafts())
        drafts.extend(self._generate_github_drafts())
        drafts.extend(self._generate_wayback_drafts())
        drafts.extend(self._generate_shodan_drafts())
        drafts.extend(self._generate_censys_drafts())
        drafts.extend(self._generate_cloud_storage_drafts())
        drafts.extend(self._generate_ct_log_drafts())
        return drafts

    def _deduplicate_drafts(
        self,
        drafts: Iterable[TechniqueDraft],
    ) -> tuple[list[TechniqueDraft], list[DuplicateRemoval]]:
        exact_signatures: dict[tuple[str, str], TechniqueDraft] = {}
        near_signatures: dict[tuple[str, tuple[str, ...]], TechniqueDraft] = {}
        names_by_category: dict[tuple[str, str], TechniqueDraft] = {}
        kept: list[TechniqueDraft] = []
        removals: list[DuplicateRemoval] = []

        for draft in drafts:
            spec = PACK_SPECS[draft.pack_key]
            exact_signature = normalized_template_signature(spec.engine, draft.query_template)
            near_signature = near_duplicate_signature(spec.engine, draft.query_template)
            normalized_name = normalize_name(draft.name)
            name_key = (spec.category_name, normalized_name)

            previous_exact = exact_signatures.get(exact_signature)
            if previous_exact is not None:
                removals.append(
                    DuplicateRemoval(
                        pack_key=draft.pack_key,
                        name=draft.name,
                        query_template=draft.query_template,
                        reason="it is an exact normalized template duplicate",
                        kept_name=previous_exact.name,
                        kept_query_template=previous_exact.query_template,
                        source=draft.source,
                    )
                )
                continue

            previous_near = near_signatures.get(near_signature)
            if (
                previous_near is not None
                and near_signature[1]
                and normalize_name(previous_near.name) == normalized_name
            ):
                removals.append(
                    DuplicateRemoval(
                        pack_key=draft.pack_key,
                        name=draft.name,
                        query_template=draft.query_template,
                        reason="it is a near-duplicate of an existing query intent",
                        kept_name=previous_near.name,
                        kept_query_template=previous_near.query_template,
                        source=draft.source,
                    )
                )
                continue

            previous_name = names_by_category.get(name_key)
            if previous_name is not None:
                removals.append(
                    DuplicateRemoval(
                        pack_key=draft.pack_key,
                        name=draft.name,
                        query_template=draft.query_template,
                        reason="its name already exists in the same category",
                        kept_name=previous_name.name,
                        kept_query_template=previous_name.query_template,
                        source=draft.source,
                    )
                )
                continue

            exact_signatures[exact_signature] = draft
            near_signatures[near_signature] = draft
            names_by_category[name_key] = draft
            kept.append(draft)

        kept.sort(key=lambda item: (PACK_SPECS[item.pack_key].display_order, item.name.lower()))
        return kept, removals

    def _draft_to_payload(self, spec: TechniquePackSpec, draft: TechniqueDraft) -> dict[str, object]:
        normalized_template = normalize_template(draft.query_template)
        template_digest = hashlib.sha1(
            f"{spec.category_id}:{normalized_template.lower()}".encode("utf-8")
        ).hexdigest()[:10]
        slug_tokens = [
            token
            for token in draft.name.lower().replace("/", " ").replace("&", " ").split()
            if token.isascii()
        ]
        slug = "-".join(
            "".join(character for character in token if character.isalnum())
            for token in slug_tokens[:6]
            if any(character.isalnum() for character in token)
        ).strip("-")
        technique_id = f"{spec.category_id.removesuffix('_queries')}-{slug or 'technique'}-{template_digest}"

        return {
            "id": technique_id,
            "name": draft.name,
            "category": spec.category_name,
            "engine": spec.engine,
            "description": draft.description,
            "query_template": normalized_template,
            "variables": [VARIABLE_LIBRARY[name] for name in draft.variables],
            "tags": sorted(dict.fromkeys(tag for tag in draft.tags if tag)),
            "example": self._build_example(normalized_template, draft.variables),
            "safe_mode": True,
            "reference": draft.reference or spec.reference,
            "launch_url": draft.launch_url or spec.launch_url,
        }

    def _build_example(self, query_template: str, variables: Iterable[str]) -> str:
        replacements = {
            variable_name: str(VARIABLE_LIBRARY[variable_name]["example"])
            for variable_name in variables
        }
        return query_template.format(**replacements)

    def _draft(
        self,
        pack_key: str,
        name: str,
        query_template: str,
        description: str,
        tags: Iterable[str],
        *,
        variables: Iterable[str] = ("domain",),
        source: str,
        launch_url: str = "",
    ) -> TechniqueDraft:
        return TechniqueDraft(
            pack_key=pack_key,
            name=name.strip(),
            query_template=normalize_template(query_template),
            description=description.strip(),
            tags=tuple(sorted(dict.fromkeys(tag.strip().lower() for tag in tags if tag.strip()))),
            variables=tuple(variables),
            source=source,
            launch_url=launch_url.strip(),
        )

    def _generate_google_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        route_terms = [
            "account/login",
            "admin",
            "admin/login.aspx",
            "admin/console",
            "admin/dashboard",
            "admin/index.php",
            "admin/login",
            "admin/login.php",
            "api/docs",
            "api/health",
            "api/status",
            "app/login",
            "auth/login",
            "auth/signin",
            "backend",
            "backend/login",
            "billing/login",
            "change-log",
            "changelog",
            "console",
            "console/login",
            "controlpanel",
            "customer-portal",
            "customer/login",
            "dashboard",
            "developer-docs",
            "developers",
            "developer-portal",
            "docs",
            "docs/api",
            "gateway",
            "graphql",
            "help",
            "help-center",
            "incidents",
            "jenkins",
            "kibana",
            "login",
            "login.php",
            "manage",
            "management",
            "monitoring",
            "oauth",
            "oauth/authorize",
            "openapi",
            "partner-portal",
            "partner/login",
            "portal",
            "portal/login",
            "redoc",
            "release-notes",
            "service-status",
            "signin",
            "siteadmin",
            "sso",
            "status",
            "statuspage",
            "support",
            "support/login",
            "swagger",
            "system/login",
            "system/status",
            "teams/login",
            "user/login",
            "user/signin",
            "vendor/login",
            "webadmin",
            "webhooks",
            "wiki",
            "wp-admin",
            "wp-login.php",
        ]
        for route in route_terms:
            label = route.replace("/", " ").replace("-", " ").replace("_", " ").title()
            tags = ["google", "recon", "admin-surface"]
            if any(term in route for term in ("login", "signin", "auth", "sso")):
                tags.append("authentication")
            if any(term in route for term in ("api", "graphql", "swagger", "openapi", "redoc", "webhooks")):
                tags.append("api-discovery")
            drafts.append(
                self._draft(
                    "google_dorks",
                    f"{label} Path Search",
                    f'site:{{domain}} inurl:"/{route}"',
                    (
                        f"Searches indexed pages on a target domain for the public route pattern "
                        f"`/{route}`. This helps identify exposed admin, login, documentation, "
                        "and application surface clues during authorized recon."
                    ),
                    tags,
                    source="generated:google-routes",
                )
            )

        titled_surfaces = [
            ("Admin Panel", "admin", ["admin-surface"]),
            ("Control Panel", "cpanel", ["admin-surface"]),
            ("Developer Console", "console", ["dashboards", "developer-tools"]),
            ("Developer Portal", "developers", ["documentation"]),
            ("Developer Documentation", "api", ["documentation", "api-discovery"]),
            ("Grafana", "login", ["dashboards", "monitoring"]),
            ("Jenkins", "dashboard", ["dashboards", "ci-cd"]),
            ("Jupyter", "tree", ["dashboards", "developer-tools"]),
            ("Kibana", "kibana", ["dashboards", "monitoring"]),
            ("OpenAPI", "api", ["documentation", "api-discovery"]),
            ("Partner Portal", "portal", ["dashboards"]),
            ("Plesk", "login", ["admin-surface"]),
            ("Prometheus", "graph", ["monitoring"]),
            ("Remote Access", "vpn", ["remote-access"]),
            ("Service Status", "status", ["status-pages"]),
            ("Sitemap", "sitemap", ["content-discovery"]),
            ("Solr Admin", "solr/admin", ["search-platform"]),
            ("Status Page", "statuspage", ["status-pages"]),
            ("Swagger UI", "swagger", ["documentation", "api-discovery"]),
            ("Tomcat", "manager", ["admin-surface"]),
            ("Webmin", "webmin", ["admin-surface"]),
            ("WordPress", "wp-admin", ["wordpress", "cms"]),
        ]
        for title, hint, tags in titled_surfaces:
            drafts.append(
                self._draft(
                    "google_dorks",
                    f"{title} Title Search",
                    f'site:{{domain}} intitle:"{title}" inurl:{hint}',
                    (
                        f"Searches indexed pages on a target domain for titles matching "
                        f"`{title}` together with route hints that support public surface mapping."
                    ),
                    ["google", "recon", *tags],
                    source="generated:google-titles",
                )
            )

        parameter_names = [
            "callback",
            "cat",
            "env",
            "filter",
            "format",
            "lang",
            "locale",
            "next",
            "page",
            "path",
            "product_id",
            "q",
            "query",
            "redirect",
            "returnUrl",
            "search",
            "service",
            "sort",
            "stage",
            "target",
            "tenant",
            "version",
            "view",
            "webhook",
        ]
        for parameter_name in parameter_names:
            label = parameter_name.replace("_", " ").title()
            tags = ["google", "recon", "indexed-parameters"]
            if parameter_name in {"version", "webhook"}:
                tags.append("api-discovery")
            drafts.append(
                self._draft(
                    "google_dorks",
                    f"{label} Parameter Search",
                    f'site:{{domain}} inurl:"?{parameter_name}="',
                    (
                        f"Searches indexed results on a target domain for URLs containing the "
                        f"`{parameter_name}` parameter. This helps identify public routes and "
                        "parameterized application surfaces."
                    ),
                    tags,
                    source="generated:google-parameters",
                )
            )

        error_terms = [
            ("Access Denied", '"access denied"'),
            ("Application Error", '"application error"'),
            ("Debug Exception", '"debug exception"'),
            ("Error 500", '"error 500"'),
            ("Exception Trace", '"exception trace"'),
            ("Fatal Error", '"fatal error"'),
            ("Gateway Error", '"bad gateway"'),
            ("Invalid Request", '"invalid request"'),
            ("Invalid Session", '"invalid session"'),
            ("Page Not Found", '"page not found"'),
            ("PHP Warning", '"php warning"'),
            ("Request ID", '"request id"'),
            ("Service Unavailable", '"service unavailable"'),
            ("Stack Trace", '"stack trace"'),
            ("Traceback", '"traceback"'),
            ("Unauthorized", '"unauthorized"'),
            ("Unexpected Error", '"unexpected error"'),
        ]
        for label, phrase in error_terms:
            drafts.append(
                self._draft(
                    "google_dorks",
                    f"{label} Search",
                    f"site:{{domain}} {phrase}",
                    (
                        f"Searches indexed pages on a target domain for the error phrase "
                        f"{phrase}. This supports public error-page discovery and environment "
                        "mapping without targeting secrets or private records."
                    ),
                    ["google", "recon", "error-pages"],
                    source="generated:google-errors",
                )
            )
        return drafts

    def _generate_api_discovery_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        api_paths = [
            "api",
            "api-docs",
            "api/documentation",
            "api/reference",
            "api/schema",
            "api/swagger",
            "api/v1",
            "api/v2",
            "api/v3",
            "callback",
            "callbacks",
            "developer",
            "developers",
            "docs/api",
            "graphql",
            "graphql/playground",
            "grpc",
            "jsonrpc",
            "openapi",
            "openapi.json",
            "openapi.yaml",
            "postman",
            "redoc",
            "rest",
            "rest/v1",
            "rest/v2",
            "rpc",
            "swagger",
            "swagger-ui",
            "webhook",
            "webhooks",
        ]
        for path in api_paths:
            label = path.replace("/", " ").replace("-", " ").replace("_", " ").title()
            drafts.append(
                self._draft(
                    "api_discovery",
                    f"{label} Search",
                    f'site:{{domain}} inurl:"/{path}"',
                    (
                        f"Searches indexed pages on a target domain for the route pattern "
                        f"`/{path}`. This helps discover public API routes, schema pages, "
                        "and developer-facing endpoints."
                    ),
                    ["google", "api", "recon", "path-discovery"],
                    source="generated:api-paths",
                )
            )

        api_files = [
            "openapi.json",
            "openapi.yaml",
            "openapi.yml",
            "swagger.json",
            "swagger.yaml",
            "swagger.yml",
            "postman_collection.json",
            "insomnia.json",
            "graphql.schema.json",
            "api-schema.json",
            "api-reference.json",
            "collection.json",
            "asyncapi.yaml",
            "asyncapi.yml",
            "redoc.html",
        ]
        for file_name in api_files:
            label = file_name.replace(".", " ").replace("_", " ").title()
            drafts.append(
                self._draft(
                    "api_discovery",
                    f"{label} File Search",
                    f"site:{{domain}} filename:{file_name}",
                    (
                        f"Searches indexed content on a target domain for the public file name "
                        f"`{file_name}`. This helps locate schema files, API collections, "
                        "and documentation artifacts."
                    ),
                    ["google", "api", "recon", "documentation"],
                    source="generated:api-files",
                )
            )

        api_keywords = [
            "developer portal",
            "api explorer",
            "api documentation",
            "schema reference",
            "rest api",
            "graphql endpoint",
            "graphql schema",
            "integration guide",
            "webhook delivery",
            "webhook signatures",
            "oauth callback",
            "api changelog",
            "service catalog",
            "sdk documentation",
            "rate limits",
        ]
        for keyword in api_keywords:
            label = keyword.title()
            drafts.append(
                self._draft(
                    "api_discovery",
                    f"{label} Search",
                    f'site:{{domain}} "{keyword}"',
                    (
                        f"Searches indexed pages on a target domain for the phrase `{keyword}`. "
                        "This helps locate public API documentation, integration details, "
                        "and developer support content."
                    ),
                    ["google", "api", "recon", "documentation"],
                    source="generated:api-keywords",
                )
            )
        return drafts

    def _generate_exposed_file_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        topic_by_extension = {
            "pdf": ["architecture", "deployment guide", "incident report", "runbook", "service catalog", "user guide", "release notes"],
            "doc": ["architecture", "operations manual", "user guide", "integration guide", "deployment checklist"],
            "docx": ["operations manual", "network diagram", "project brief", "service catalog", "endpoint inventory"],
            "xls": ["asset inventory", "release notes", "site map", "status report", "service list"],
            "xlsx": ["asset inventory", "status report", "service catalog", "change log", "inventory report"],
            "csv": ["asset inventory", "host list", "service list", "subdomain list", "endpoint inventory"],
            "txt": ["changelog", "deployment guide", "runbook", "status notes", "service catalog"],
            "log": ["error", "access denied", "service unavailable", "stack trace", "application error"],
            "json": ["manifest", "status page", "service catalog", "release notes", "site map"],
            "xml": ["sitemap", "feed", "service index", "release notes", "asset index"],
            "yaml": ["deployment guide", "service catalog", "operations manual", "release plan"],
            "yml": ["deployment guide", "operations manual", "service catalog", "release plan"],
        }
        for extension, topics in topic_by_extension.items():
            for topic in topics:
                label = f"{topic.title()} {extension.upper()}"
                drafts.append(
                    self._draft(
                        "exposed_files",
                        f"{label} Search",
                        f'site:{{domain}} filetype:{extension} "{topic}"',
                        (
                            f"Searches indexed content on a target domain for `{topic}` "
                            f"inside public `{extension}` files. This supports safe discovery "
                            "of documents, reports, and operational references."
                        ),
                        ["google", "files", "recon", "documents"],
                        source="generated:exposed-files",
                    )
                )

        directory_terms = [
            "archive",
            "assets",
            "backup",
            "build",
            "downloads",
            "docs",
            "downloads",
            "exports",
            "files",
            "guides",
            "htdocs",
            "images",
            "logs",
            "manuals",
            "media",
            "packages",
            "public",
            "releases",
            "reports",
            "revisions",
            "snapshots",
            "source",
            "src",
            "static",
            "uploads",
            "wwwroot",
        ]
        for term in directory_terms:
            label = term.replace("-", " ").title()
            drafts.append(
                self._draft(
                    "exposed_files",
                    f"{label} Directory Listing Search",
                    f'site:{{domain}} intitle:"index of" "{term}"',
                    (
                        f"Searches for indexed directory listing pages on a target domain "
                        f"that reference `{term}`. This helps find public directories, "
                        "release archives, and browsable asset locations."
                    ),
                    ["google", "files", "recon", "directory-listing"],
                    source="generated:directory-listings",
                )
            )

        backup_extensions = ["7z", "bak", "backup", "bundle", "gz", "old", "rar", "tar", "tgz", "zip"]
        backup_terms = ["archive", "backup", "bundle", "export", "release", "snapshot"]
        for extension in backup_extensions:
            for term in backup_terms:
                drafts.append(
                    self._draft(
                        "exposed_files",
                        f"{term.title()} {extension.upper()} Search",
                        f"site:{{domain}} ext:{extension} {term}",
                        (
                            f"Searches indexed results on a target domain for `{extension}` files "
                            f"that mention `{term}`. This supports safe discovery of public "
                            "backup-like artifacts and release bundles."
                        ),
                        ["google", "files", "recon", "backups"],
                        source="generated:backup-artifacts",
                    )
                )
        return drafts

    def _generate_cms_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        cms_patterns = {
            "WordPress": [
                "wp-admin",
                "wp-admin/admin-ajax.php",
                "wp-content",
                "wp-content/plugins",
                "wp-content/themes",
                "wp-content/uploads",
                "wp-includes",
                "wp-json",
                "wp-json/oembed",
                "wp-json/wp/v2/posts",
                "wp-json/wp/v2/types",
                "wp-json/wp/v2/pages",
                "wp-json/wp/v2/tags",
                "wp-json/wp/v2/categories",
                "wp-login.php",
                "xmlrpc.php",
                "license.txt",
                "readme.html",
                "wp-cron.php",
                "feed",
                "sitemap_index.xml",
                "author-sitemap.xml",
                "wp-sitemap.xml",
                "wp-content/cache",
                "robots.txt wordpress",
                'intext:"powered by wordpress"',
            ],
            "Joomla": [
                "administrator",
                "administrator/index.php",
                "api/index.php",
                "component/users",
                "com_content",
                "com_contact",
                "com_search",
                "com_ajax",
                "index.php?option=com_",
                "joomla.xml",
                "language/en-GB",
                "templates/protostar",
                "templates/cassiopeia",
                "media/system",
                "robots.txt joomla",
            ],
            "Drupal": [
                "user/login",
                "user/register",
                "sites/default/files",
                "sites/all/modules",
                "sites/all/themes",
                "sites/default/settings.php",
                "drupal",
                "index.php?q=user/login",
                "CHANGELOG.txt",
                "robots.txt drupal",
                'intext:"powered by drupal"',
                "core/modules",
                "core/assets",
                "sites/default/files/js",
            ],
            "Magento": [
                "admin",
                "downloader",
                "customer/account/login",
                "catalogsearch",
                "static/frontend",
                "pub/static",
                "magento",
                "release-notes",
                "rest/default/V1",
                "graphql magento",
                "robots.txt magento",
                'intext:"powered by magento"',
            ],
            "Laravel": [
                "laravel",
                "storage/framework",
                "mix-manifest.json",
                "vendor/laravel",
                "horizon",
                "telescope",
                "sanctum/csrf-cookie",
                "livewire",
                "nova",
                "api/documentation laravel",
                "routes/web.php laravel",
                "routes/api.php laravel",
            ],
            "Django": [
                "admin/login",
                "django",
                "__debug__",
                "static/admin",
                "accounts/login",
                "robots.txt django",
                'intext:"Django administration"',
                "sitemap.xml django",
                "rest framework",
                "drf-yasg",
                "openapi django",
                "swagger django",
            ],
            "Ghost": [
                "ghost",
                "ghost/api",
                "ghost/#/signin",
                "content/images",
                "robots.txt ghost",
                "ghost/members",
                "ghost/assets",
            ],
            "Strapi": [
                "strapi",
                "admin/init",
                "content-manager",
                "content-type-builder",
                "upload/files",
                "documentation strapi",
                "openapi strapi",
                "graphql strapi",
            ],
        }
        for cms_name, patterns in cms_patterns.items():
            cms_tag = cms_name.lower().replace(" ", "-")
            for pattern in patterns:
                label = pattern.replace("/", " ").replace("_", " ").replace("-", " ").title()
                drafts.append(
                    self._draft(
                        "cms_queries",
                        f"{cms_name} {label} Search",
                        f'site:{{domain}} "{pattern}"',
                        (
                            f"Searches indexed pages on a target domain for the `{pattern}` "
                            f"surface associated with {cms_name}. This helps identify public "
                            "CMS components, uploads, admin routes, and implementation clues."
                        ),
                        ["google", "cms", cms_tag, "recon"],
                        source=f"generated:cms-{cms_tag}",
                    )
                )
        return drafts

    def _generate_github_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        domain_file_patterns = [
            "filename:config.json",
            "filename:application.yml",
            "filename:settings.json",
            "filename:values.yaml",
            "filename:helmfile.yaml",
            "filename:kustomization.yaml",
            "filename:Dockerfile",
            "filename:docker-compose.yml",
            "filename:terraform.tfvars",
            "filename:main.tf",
            "filename:package.json",
            "filename:pyproject.toml",
            "filename:requirements.txt",
            "filename:composer.json",
            "filename:pom.xml",
            "filename:build.gradle",
            "filename:nginx.conf",
            "filename:Caddyfile",
            "filename:traefik.yml",
            "path:.github/workflows",
            "filename:.gitlab-ci.yml",
            "filename:Jenkinsfile",
            "path:/docs/",
            "filename:mkdocs.yml",
            "filename:docusaurus.config.js",
            "filename:openapi.yaml",
            "filename:swagger.json",
            "filename:statuspage.yml",
            "filename:runbook.md",
            "filename:incident-response.md",
            "filename:inventory.csv",
            "filename:service-map.json",
            "filename:zone.tf",
            "filename:ingress.yaml",
            "filename:prometheus.yml",
        ]
        for pattern in domain_file_patterns:
            label = (
                pattern.replace("filename:", "")
                .replace("path:", "")
                .replace("/", " ")
                .replace(".", " ")
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )
            drafts.append(
                self._draft(
                    "github_queries",
                    f"Domain {label} Search",
                    f'"{{domain}}" {pattern}',
                    (
                        f"Searches public GitHub code for a target domain together with the "
                        f"`{pattern}` hint. This helps identify public configuration, workflow, "
                        "and documentation references tied to the target."
                    ),
                    ["github", "domain-references", "recon", "public-code"],
                    source="generated:github-domain",
                )
            )

        company_patterns = [
            "path:/docs/",
            "path:.github/workflows",
            "filename:README.md",
            "filename:mkdocs.yml",
            "filename:docker-compose.yml",
            "filename:kustomization.yaml",
            "filename:helmfile.yaml",
            "filename:values.yaml",
            "filename:main.tf",
            "filename:package.json",
            "filename:pyproject.toml",
            "filename:nginx.conf",
            "filename:statuspage.yml",
            "filename:incident-response.md",
            "filename:runbook.md",
            "filename:openapi.yaml",
            "filename:swagger.json",
            "filename:inventory.csv",
            "filename:service-map.json",
            "filename:ingress.yaml",
            "filename:prometheus.yml",
        ]
        for pattern in company_patterns:
            label = (
                pattern.replace("filename:", "")
                .replace("path:", "")
                .replace("/", " ")
                .replace(".", " ")
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )
            drafts.append(
                self._draft(
                    "github_queries",
                    f"Company {label} Search",
                    f'"{{company}}" {pattern}',
                    (
                        f"Searches public GitHub repositories for a company name together with "
                        f"`{pattern}`. This helps surface public workflows, docs, and deployment "
                        "material associated with the target."
                    ),
                    ["github", "company", "recon", "documentation"],
                    variables=("company",),
                    source="generated:github-company",
                )
            )

        org_queries = [
            ("API Surface", 'org:{org} (swagger OR openapi OR graphql)', ["api-discovery", "graphql", "openapi"]),
            ("CI Workflow", 'org:{org} path:.github/workflows', ["ci-cd", "workflows"]),
            ("Container Search", 'org:{org} (filename:Dockerfile OR filename:docker-compose.yml)', ["containers", "deployment"]),
            ("DNS Reference", 'org:{org} ("{org}" AND (filename:zone OR filename:named.conf))', ["dns", "configuration"]),
            ("Documentation Search", 'org:{org} (filename:README.md OR path:/docs/)', ["documentation", "public-code"]),
            ("Helm Search", 'org:{org} (filename:Chart.yaml OR filename:values.yaml)', ["kubernetes", "helm"]),
            ("Incident Runbook", 'org:{org} (filename:runbook.md OR filename:incident-response.md)', ["operations", "runbooks"]),
            ("Kubernetes Search", 'org:{org} (filename:kustomization.yaml OR filename:ingress.yaml)', ["kubernetes", "deployment"]),
            ("Monitoring Search", 'org:{org} (grafana OR prometheus OR loki)', ["monitoring", "dashboards"]),
            ("OpenAPI Search", 'org:{org} (filename:openapi.yaml OR filename:swagger.json)', ["api-discovery", "documentation"]),
            ("Service Map Search", 'org:{org} (filename:service-map.json OR filename:inventory.csv)', ["inventory", "mapping"]),
            ("Terraform Search", 'org:{org} (filename:main.tf OR filename:terraform.tfvars)', ["terraform", "infrastructure-as-code"]),
        ]
        for label, query_template, tags in org_queries:
            drafts.append(
                self._draft(
                    "github_queries",
                    f"Org {label} Search",
                    query_template,
                    (
                        f"Searches public GitHub repositories inside the `{label}` family for "
                        "organization-owned repositories and public infrastructure clues."
                    ),
                    ["github", "organization", "recon", *tags],
                    variables=("org",),
                    source="generated:github-org",
                )
            )

        keyword_patterns = [
            "filename:docker-compose.yml",
            "filename:helmfile.yaml",
            "filename:kustomization.yaml",
            "filename:openapi.yaml",
            "filename:openapi.json",
            "filename:swagger.json",
            "filename:swagger.yaml",
            "filename:README.md",
            "filename:runbook.md",
            "filename:statuspage.yml",
            "filename:terraform.tfvars",
            "filename:package.json",
            "filename:pyproject.toml",
            "path:/docs/",
            "path:.github/workflows",
        ]
        for pattern in keyword_patterns:
            label = (
                pattern.replace("filename:", "")
                .replace("path:", "")
                .replace("/", " ")
                .replace(".", " ")
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )
            drafts.append(
                self._draft(
                    "github_queries",
                    f"Keyword {label} Search",
                    f'"{{keyword}}" {pattern}',
                    (
                        f"Searches public GitHub repositories for a keyword together with `{pattern}`. "
                        "This helps find product references, public workflows, and deployment patterns."
                    ),
                    ["github", "keyword-search", "recon", "public-code"],
                    variables=("keyword",),
                    source="generated:github-keyword",
                )
            )
        return drafts

    def _generate_wayback_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        archive_paths = [
            ("Admin Path History", "admin", "admin-surface"),
            ("API V1 History", "api/v1", "api-discovery"),
            ("API V2 History", "api/v2", "api-discovery"),
            ("API Path History", "api", "api-discovery"),
            ("Assets Path History", "assets", "assets"),
            ("Auth Path History", "auth", "authentication"),
            ("Backup Path History", "backup", "backups"),
            ("Build Path History", "build", "assets"),
            ("Callback History", "callback", "api-discovery"),
            ("Change Log History", "changelog", "documentation"),
            ("Docs History", "docs", "documentation"),
            ("Download History", "download", "files"),
            ("GraphQL Path History", "graphql", "api-discovery"),
            ("Health Endpoint History", "health", "monitoring"),
            ("Integrations History", "integrations", "documentation"),
            ("Login Path History", "login", "authentication"),
            ("OpenAPI JSON History", "openapi.json", "api-discovery"),
            ("OpenAPI History", "openapi", "api-discovery"),
            ("Partner Path History", "partner", "dashboards"),
            ("Portal History", "portal", "dashboards"),
            ("Redoc History", "redoc", "api-discovery"),
            ("Release Notes History", "release-notes", "documentation"),
            ("Robots.txt History", "robots.txt", "content-discovery"),
            ("SDK History", "sdk", "documentation"),
            ("Sitemap History", "sitemap", "content-discovery"),
            ("Static Assets History", "static", "assets"),
            ("Status History", "status", "monitoring"),
            ("Swagger History", "swagger", "api-discovery"),
            ("Swagger JSON History", "swagger.json", "api-discovery"),
            ("Swagger UI History", "swagger-ui", "api-discovery"),
            ("Upload Path History", "upload", "files"),
            ("Version Endpoint History", "version", "api-discovery"),
            ("Webhook History", "webhook", "api-discovery"),
            ("Well-Known Path History", ".well-known", "content-discovery"),
        ]
        for label, path_hint, tag in archive_paths:
            drafts.append(
                self._draft(
                    "wayback_queries",
                    label,
                    f"{{domain}} archived {path_hint} history",
                    (
                        f"Opens archived captures for a target domain whose URL history includes "
                        f"`{path_hint}`. This helps discover historical routes and public content "
                        "no longer visible on the live site."
                    ),
                    ["wayback", "archive", "historical-recon", tag],
                    source="generated:wayback-paths",
                    launch_url=f"https://web.archive.org/web/*/{{domain}}/*{path_hint}*",
                )
            )

        subdomain_prefixes = [
            "admin",
            "api",
            "assets",
            "auth",
            "beta",
            "blog",
            "cdn",
            "console",
            "dev",
            "developer",
            "docs",
            "edge",
            "git",
            "help",
            "id",
            "login",
            "media",
            "mobile",
            "partners",
            "portal",
            "preview",
            "search",
            "shop",
            "stage",
            "static",
            "status",
            "support",
            "vpn",
        ]
        for prefix in subdomain_prefixes:
            label = prefix.title()
            drafts.append(
                self._draft(
                    "wayback_queries",
                    f"{label} Host History",
                    f"{prefix}.{{domain}} archived history",
                    (
                        f"Opens archived captures for the `{prefix}.{{domain}}` host pattern. "
                        "This helps identify historical subdomain usage and retired public hosts."
                    ),
                    ["wayback", "archive", "subdomains", "historical-recon"],
                    source="generated:wayback-hosts",
                    launch_url=f"https://web.archive.org/web/*/{prefix}.{{domain}}/*",
                )
            )
        return drafts

    def _generate_shodan_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        domain_filters = [
            ("Hostname", "hostname:{domain}", ["hostname", "asset-discovery"]),
            ("SSL String", 'ssl:"{domain}"', ["ssl", "certificates"]),
            ("HTTP HTML", 'hostname:{domain} http.html:"{domain}"', ["html-content", "branding"]),
            ("HTTP Title", 'hostname:{domain} http.title:"{domain}"', ["http-titles", "branding"]),
            ("Product", 'hostname:{domain} product:"{domain}"', ["product", "fingerprinting"]),
        ]
        for label, query_template, tags in domain_filters:
            drafts.append(
                self._draft(
                    "shodan_queries",
                    f"{label} Domain Search",
                    query_template,
                    (
                        f"Searches Shodan for `{label.lower()}` data associated with a target domain. "
                        "This supports internet-facing asset discovery and surface review."
                    ),
                    ["shodan", "recon", *tags],
                    source="generated:shodan-domain",
                )
            )

        company_filters = [
            ("Organization", 'org:"{company}"', ["organization", "inventory"]),
            ("HTTP Title", 'http.title:"{company}"', ["http-titles", "branding"]),
            ("HTTP HTML", 'http.html:"{company}"', ["html-content", "branding"]),
            ("Product Reference", 'product:"{company}"', ["product", "fingerprinting"]),
            ("SSL Reference", 'ssl:"{company}"', ["ssl", "branding"]),
        ]
        for label, query_template, tags in company_filters:
            drafts.append(
                self._draft(
                    "shodan_queries",
                    f"{label} Company Search",
                    query_template,
                    (
                        f"Searches Shodan for `{label.lower()}` fields that reference the target company. "
                        "This helps identify branded or organization-linked public systems."
                    ),
                    ["shodan", "recon", *tags],
                    variables=("company",),
                    source="generated:shodan-company",
                )
            )

        scoped_service_terms = [
            ("Admin Portal", "admin", ["admin-surface"]),
            ("API", "api", ["api-discovery"]),
            ("Dashboard", "dashboard", ["dashboards"]),
            ("Developer Portal", "developer portal", ["documentation"]),
            ("Grafana", "grafana", ["monitoring"]),
            ("Jenkins", "jenkins", ["ci-cd"]),
            ("Kibana", "kibana", ["monitoring"]),
            ("Login", "login", ["authentication"]),
            ("Monitoring", "monitoring", ["monitoring"]),
            ("OpenAPI", "openapi", ["api-discovery"]),
            ("Portal", "portal", ["dashboards"]),
            ("Prometheus", "prometheus", ["monitoring"]),
            ("Redoc", "redoc", ["api-discovery"]),
            ("Remote Access", "remote access", ["remote-access"]),
            ("Status", "status", ["monitoring"]),
            ("Swagger", "swagger", ["api-discovery"]),
        ]
        shodan_domain_fields = [
            ("HTML", 'hostname:{domain} http.html:"{term}"', ["html-content", "keyword-search"]),
            ("Title", 'hostname:{domain} http.title:"{term}"', ["http-titles", "keyword-search"]),
            ("SSL", 'hostname:{domain} ssl:"{term}"', ["ssl", "keyword-search"]),
        ]
        for label, term, tags in scoped_service_terms:
            for field_label, query_template, field_tags in shodan_domain_fields:
                drafts.append(
                    self._draft(
                        "shodan_queries",
                        f"{label} {field_label} Domain Search",
                        query_template.replace("{term}", term),
                        (
                            f"Searches Shodan for target-domain hosts whose {field_label.lower()} data references "
                            f"`{term}`. This helps review internet-facing services tied to that target."
                        ),
                        ["shodan", "recon", *tags, *field_tags],
                        source="generated:shodan-scoped-domain",
                    )
                )

        organization_terms = [
            ("Admin", "admin", ["admin-surface"]),
            ("API", "api", ["api-discovery"]),
            ("Documentation", "docs", ["documentation"]),
            ("Grafana", "grafana", ["monitoring"]),
            ("Jenkins", "jenkins", ["ci-cd"]),
            ("Portal", "portal", ["dashboards"]),
            ("Status", "status", ["monitoring"]),
            ("Support", "support", ["support"]),
        ]
        shodan_company_fields = [
            ("Title", 'org:"{company}" http.title:"{term}"', ["http-titles", "organization"]),
            ("HTML", 'org:"{company}" http.html:"{term}"', ["html-content", "organization"]),
        ]
        for label, term, tags in organization_terms:
            for field_label, query_template, field_tags in shodan_company_fields:
                drafts.append(
                    self._draft(
                        "shodan_queries",
                        f"{label} {field_label} Company Search",
                        query_template.replace("{term}", term),
                        (
                            f"Searches Shodan for organization-linked systems whose {field_label.lower()} "
                            f"data references `{term}`. This supports branded service inventory review."
                        ),
                        ["shodan", "recon", *tags, *field_tags],
                        variables=("company",),
                        source="generated:shodan-scoped-company",
                    )
                )
        return drafts

    def _generate_censys_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        domain_queries = [
            ("Certificate Common Name", "services.tls.certificates.leaf_data.subject.common_name: {domain}", ["certificates", "tls"]),
            ("Certificate SAN", "services.tls.certificates.leaf_data.names: {domain}", ["certificates", "subject-alt-name"]),
            ("HTTP HTML Body", "services.http.response.body: {domain}", ["http", "html-content"]),
            ("Observed Hostname", "dns.names: {domain}", ["dns", "hostnames"]),
            ("Service Banner", "services.banner: {domain}", ["service-banners", "fingerprinting"]),
        ]
        for label, query_template, tags in domain_queries:
            drafts.append(
                self._draft(
                    "censys_queries",
                    f"{label} Domain Search",
                    query_template,
                    (
                        f"Searches Censys host data for `{label.lower()}` values related to a target domain. "
                        "This supports public asset discovery and certificate correlation."
                    ),
                    ["censys", "recon", *tags],
                    source="generated:censys-domain",
                )
            )

        company_queries = [
            ("HTTP Title", "services.http.response.html_title: {company}", ["http", "titles", "branding"]),
            ("Banner", "services.banner: {company}", ["service-banners", "branding"]),
            ("Certificate Subject", "services.tls.certificates.leaf_data.subject.organization: {company}", ["certificates", "organization"]),
            ("Issuer Organization", "services.tls.certificates.leaf_data.issuer.organization: {company}", ["certificates", "issuer"]),
            ("Observed Domain", "dns.reverse_dns.names: {company}", ["dns", "reverse-dns"]),
        ]
        for label, query_template, tags in company_queries:
            drafts.append(
                self._draft(
                    "censys_queries",
                    f"{label} Company Search",
                    query_template,
                    (
                        f"Searches Censys for `{label.lower()}` records that reference the target company. "
                        "This helps find branded public systems and certificate metadata."
                    ),
                    ["censys", "recon", *tags],
                    variables=("company",),
                    source="generated:censys-company",
                )
            )

        scoped_terms = [
            ("Admin", "admin", ["admin-surface"]),
            ("API", "api", ["api-discovery"]),
            ("Dashboard", "dashboard", ["dashboards"]),
            ("Developer Portal", "developer portal", ["documentation"]),
            ("Grafana", "grafana", ["monitoring"]),
            ("Jenkins", "jenkins", ["ci-cd"]),
            ("Kibana", "kibana", ["monitoring"]),
            ("Login", "login", ["authentication"]),
            ("Monitoring", "monitoring", ["monitoring"]),
            ("OpenAPI", "openapi", ["api-discovery"]),
            ("Portal", "portal", ["dashboards"]),
            ("Prometheus", "prometheus", ["monitoring"]),
            ("Redoc", "redoc", ["api-discovery"]),
            ("Status", "status", ["monitoring"]),
            ("Swagger", "swagger", ["api-discovery"]),
            ("Support", "support", ["support"]),
        ]
        censys_domain_fields = [
            (
                "Banner",
                'dns.names: {domain} and services.banner: "{term}"',
                ["service-banners", "hostnames"],
            ),
            (
                "HTTP Title",
                'dns.names: {domain} and services.http.response.html_title: "{term}"',
                ["titles", "http"],
            ),
            (
                "HTTP Body",
                'dns.names: {domain} and services.http.response.body: "{term}"',
                ["html-content", "http"],
            ),
        ]
        for label, term, tags in scoped_terms:
            for field_label, query_template, field_tags in censys_domain_fields:
                drafts.append(
                    self._draft(
                        "censys_queries",
                        f"{label} {field_label} Domain Search",
                        query_template.replace("{term}", term),
                        (
                            f"Searches Censys for target-domain hosts whose {field_label.lower()} data references "
                            f"`{term}`. This supports public surface discovery and service review."
                        ),
                        ["censys", "recon", *tags, *field_tags],
                        source="generated:censys-scoped-domain",
                    )
                )

        censys_company_terms = [
            ("Admin", "admin", ["admin-surface"]),
            ("API", "api", ["api-discovery"]),
            ("Documentation", "docs", ["documentation"]),
            ("Grafana", "grafana", ["monitoring"]),
            ("Portal", "portal", ["dashboards"]),
            ("Status", "status", ["monitoring"]),
            ("Support", "support", ["support"]),
            ("Swagger", "swagger", ["api-discovery"]),
        ]
        censys_company_fields = [
            (
                "HTTP Title",
                'services.http.response.html_title: "{term}" and services.tls.certificates.leaf_data.subject.organization: "{company}"',
                ["titles", "organization"],
            ),
            (
                "Banner",
                'services.banner: "{term}" and services.tls.certificates.leaf_data.subject.organization: "{company}"',
                ["service-banners", "organization"],
            ),
        ]
        for label, term, tags in censys_company_terms:
            for field_label, query_template, field_tags in censys_company_fields:
                drafts.append(
                    self._draft(
                        "censys_queries",
                        f"{label} {field_label} Company Search",
                        query_template.replace("{term}", term),
                        (
                            f"Searches Censys for organization-linked services whose {field_label.lower()} "
                            f"data references `{term}`. This helps surface branded or operational systems."
                        ),
                        ["censys", "recon", *tags, *field_tags],
                        variables=("company",),
                        source="generated:censys-scoped-company",
                    )
                )
        return drafts

    def _generate_cloud_storage_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        provider_patterns = [
            ("Amazon S3", "(site:s3.amazonaws.com OR site:amazonaws.com)", "s3"),
            ("Google Cloud Storage", "site:storage.googleapis.com", "gcs"),
            ("Azure Blob", "(site:blob.core.windows.net OR site:dfs.core.windows.net)", "azure"),
            ("DigitalOcean Spaces", "site:digitaloceanspaces.com", "spaces"),
            ("Wasabi", "site:s3.wasabisys.com", "wasabi"),
            ("Cloudflare R2", "site:r2.cloudflarestorage.com", "r2"),
        ]
        focus_terms = [
            "archive",
            "assets",
            "artifacts",
            "backup",
            "build",
            "cdn",
            "customer exports",
            "data feeds",
            "documentation",
            "downloads",
            "images",
            "manuals",
            "media",
            "openapi",
            "packages",
            "public files",
            "releases",
            "reports",
            "screenshots",
            "sitemaps",
            "snapshots",
            "static",
            "support",
            "temporary",
            "uploads",
        ]
        for provider_name, provider_query, provider_tag in provider_patterns:
            for focus_term in focus_terms:
                label = f"{provider_name} {focus_term.title()} Reference"
                drafts.append(
                    self._draft(
                        "cloud_storage",
                        f"{label} Search",
                        f'"{{company}}" "{focus_term}" {provider_query}',
                        (
                            f"Searches indexed references to {provider_name} together with the "
                            f"phrase `{focus_term}` and a target company name. This helps locate "
                            "public storage references and downloadable asset locations."
                        ),
                        ["cloud", provider_tag, "storage", "google", "references"],
                        variables=("company",),
                        source="generated:cloud-company",
                    )
                )

            drafts.append(
                self._draft(
                    "cloud_storage",
                    f"{provider_name} Domain Reference Search",
                    f'"{{domain}}" {provider_query}',
                    (
                        f"Searches indexed references to {provider_name} that also contain the target domain. "
                        "This helps identify public storage paths, screenshots, and documentation tied to the host."
                    ),
                    ["cloud", provider_tag, "storage", "google", "domain-references"],
                    source="generated:cloud-domain",
                )
            )

            drafts.append(
                self._draft(
                    "cloud_storage",
                    f"{provider_name} Keyword Reference Search",
                    f'"{{keyword}}" {provider_query}',
                    (
                        f"Searches indexed references to {provider_name} that also contain a keyword or product name. "
                        "This helps surface public file paths, asset references, and bucket naming clues."
                    ),
                    ["cloud", provider_tag, "storage", "google", "keyword-search"],
                    variables=("keyword",),
                    source="generated:cloud-keyword",
                )
            )
        return drafts

    def _generate_ct_log_drafts(self) -> list[TechniqueDraft]:
        drafts: list[TechniqueDraft] = []
        prefixes = [
            "admin",
            "api",
            "app",
            "assets",
            "auth",
            "beta",
            "blog",
            "cdn",
            "console",
            "cpanel",
            "customers",
            "dev",
            "developers",
            "docs",
            "download",
            "edge",
            "gateway",
            "git",
            "grafana",
            "help",
            "id",
            "img",
            "jenkins",
            "kibana",
            "login",
            "mail",
            "media",
            "mobile",
            "monitoring",
            "partners",
            "portal",
            "prod",
            "remote",
            "search",
            "shop",
            "smtp",
            "sso",
            "stage",
            "staging",
            "static",
            "status",
            "support",
            "test",
            "upload",
            "vpn",
            "webmail",
            "wiki",
            "www",
        ]
        for prefix in prefixes:
            label = prefix.title()
            drafts.append(
                self._draft(
                    "ct_logs",
                    f"{label} Host Certificate Search",
                    f"{prefix}.{{domain}}",
                    (
                        f"Searches certificate transparency records for `{prefix}.{{domain}}`. "
                        "This helps identify current or historical hostnames that appeared in "
                        "public certificate issuance."
                    ),
                    ["ct-logs", "crt-sh", "certificates", "subdomains", "history"],
                    source="generated:ct-prefixes",
                    launch_url=f"https://crt.sh/?q={prefix}.{{domain}}",
                )
            )

        special_queries = [
            ("Wildcard Certificate Search", "%.{domain}", ["wildcard", "certificates", "subdomains"], ("domain",)),
            ("Wildcard API Certificate Search", "%.api.{domain}", ["wildcard", "api-discovery", "subdomains"], ("domain",)),
            ("Wildcard Dev Certificate Search", "%.dev.{domain}", ["wildcard", "environments", "subdomains"], ("domain",)),
            ("Wildcard Stage Certificate Search", "%.stage.{domain}", ["wildcard", "environments", "subdomains"], ("domain",)),
            ("Wildcard Status Certificate Search", "%.status.{domain}", ["wildcard", "monitoring", "subdomains"], ("domain",)),
            ("Wildcard VPN Certificate Search", "%.vpn.{domain}", ["wildcard", "remote-access", "subdomains"], ("domain",)),
            ("Organization String Search", "{org}", ["organization", "certificate-subjects", "brand-monitoring"], ("org",)),
            ("Domain Search", "{domain}", ["domain", "certificates", "history"], ("domain",)),
        ]
        for name, query_template, tags, variables in special_queries:
            drafts.append(
                self._draft(
                    "ct_logs",
                    name,
                    query_template,
                    (
                        "Searches certificate transparency records for public certificate "
                        "metadata tied to the target string."
                    ),
                    ["ct-logs", "crt-sh", *tags],
                    variables=variables,
                    source="generated:ct-special",
                    launch_url="https://crt.sh/?q={query}",
                )
            )
        return drafts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the bundled DorkVault technique catalog from raw and curated sources."
    )
    parser.add_argument("source_file", type=Path, help="Path to the raw text collection.")
    parser.add_argument("output_dir", type=Path, help="Directory where the pack JSON files will be written.")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path for a markdown catalog build report.",
    )
    args = parser.parse_args(argv)

    builder = TechniqueCatalogBuilder()
    report = builder.build(
        args.source_file,
        args.output_dir,
        report_path=args.report,
    )

    print(
        f"Built {report.final_count} technique(s) across "
        f"{len(report.imported_by_file)} pack file(s)."
    )
    for file_name, count in sorted(report.imported_by_file.items()):
        print(f"- {file_name}: {count}")
    if args.report is not None:
        print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
