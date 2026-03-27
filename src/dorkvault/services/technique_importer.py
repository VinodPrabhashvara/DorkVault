"""Import semi-structured text collections into DorkVault technique packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_SECTION_RE = re.compile(r"^\[(?P<number>\d+)\]\s+(?P<title>.+?)\s*$")
_SUBSECTION_RE = re.compile(r"^---\s*(?P<title>.+?)\s*---$")
_DECORATION_RE = re.compile(r"^[=\-━]{4,}$")
_WHITESPACE_RE = re.compile(r"\s+")
_EXAMPLE_DOMAIN_RE = re.compile(r"\bexample\.com\b", re.IGNORECASE)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_VARIABLE_RE = re.compile(r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(slots=True, frozen=True)
class ImportCategorySpec:
    file_name: str
    category_id: str
    category_name: str
    description: str
    display_order: int
    engine: str
    launch_url: str
    reference: str


@dataclass(slots=True, frozen=True)
class RawCollectionEntry:
    line_number: int
    section_number: int
    section_title: str
    subsection_title: str
    raw_query: str


@dataclass(slots=True, frozen=True)
class ImportExclusion:
    line_number: int
    section_title: str
    subsection_title: str
    raw_query: str
    reason: str


@dataclass(slots=True, frozen=True)
class ImportedTechniqueRecord:
    file_name: str
    payload: dict[str, Any]


@dataclass(slots=True)
class TechniqueImportReport:
    source_file: str
    output_dir: str
    imported_by_file: dict[str, int] = field(default_factory=dict)
    exclusions: list[ImportExclusion] = field(default_factory=list)

    @property
    def imported_count(self) -> int:
        return sum(self.imported_by_file.values())


_CATEGORY_SPECS: dict[str, ImportCategorySpec] = {
    "google_dorks": ImportCategorySpec(
        file_name="google_dorks.json",
        category_id="google_dorks",
        category_name="Google Dorks",
        description=(
            "Target-scoped Google search techniques for public asset discovery, "
            "admin surface mapping, technology fingerprinting, and error leakage review."
        ),
        display_order=10,
        engine="Google",
        launch_url="https://www.google.com/search?q={query}",
        reference="https://support.google.com/websearch/answer/2466433",
    ),
    "api_discovery": ImportCategorySpec(
        file_name="api_discovery.json",
        category_id="api_discovery",
        category_name="API Discovery",
        description=(
            "Search engine techniques for finding public API routes, developer documentation, "
            "versioned endpoints, and related application surfaces."
        ),
        display_order=80,
        engine="Google",
        launch_url="https://www.google.com/search?q={query}",
        reference="https://support.google.com/websearch/answer/2466433",
    ),
    "exposed_files": ImportCategorySpec(
        file_name="exposed_files.json",
        category_id="exposed_files",
        category_name="Exposed Files",
        description=(
            "Target-scoped file and directory discovery searches for public documents, logs, "
            "exports, and browsable directory listings."
        ),
        display_order=70,
        engine="Google",
        launch_url="https://www.google.com/search?q={query}",
        reference="https://support.google.com/websearch/answer/2466433",
    ),
    "cms_queries": ImportCategorySpec(
        file_name="cms_queries.json",
        category_id="cms_queries",
        category_name="CMS Queries",
        description=(
            "Search queries for discovering public WordPress, Joomla, Drupal, Magento, "
            "Laravel, and Django surfaces on authorized targets."
        ),
        display_order=65,
        engine="Google",
        launch_url="https://www.google.com/search?q={query}",
        reference="https://support.google.com/websearch/answer/2466433",
    ),
}

_WHOLE_SECTION_EXCLUSIONS = {
    "OPEN CAMERAS & IOT DEVICES": (
        "Excluded because the section focuses on internet-exposed cameras and device interfaces "
        "rather than target-scoped recon techniques appropriate for the built-in catalog."
    ),
    "EXPOSED CREDENTIALS & API KEYS": (
        "Excluded because the section explicitly targets secrets, tokens, credentials, and private keys."
    ),
    "EMAIL & PERSONAL DATA": (
        "Excluded because the section targets personal data and other sensitive records."
    ),
    "OSINT / SOCIAL ENGINEERING": (
        "Excluded because the section centers on social engineering and sensitive third-party content."
    ),
    "ADVANCED GOOGLE OPERATORS REFERENCE": (
        "Excluded because the section is an operator cheat sheet, not a list of importable techniques."
    ),
}

_BLOCKED_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    ("password", "Targets passwords or password-bearing content."),
    ("secret", "Targets secrets or secret-bearing content."),
    ("token", "Targets tokens or authentication material."),
    ("private key", "Targets private key material."),
    ("api_key", "Targets API key material."),
    ("access_key", "Targets access key material."),
    ("client_secret", "Targets client secrets."),
    ("consumer_secret", "Targets client secrets."),
    ("oauth", "Targets OAuth credentials."),
    ("bearer", "Targets bearer tokens."),
    ("authorization:", "Targets authorization headers."),
    ("ssn", "Targets personal data."),
    ("social security", "Targets personal data."),
    ("credit card", "Targets payment data."),
    ("passport number", "Targets personal data."),
    ("date of birth", "Targets personal data."),
    ("personal information", "Targets personal data."),
    ("customer list", "Targets personal data."),
    ("employee list", "Targets personal data."),
    ("member list", "Targets personal data."),
    ("contact list", "Targets personal data."),
    ("resume", "Targets personal data."),
    ("curriculum vitae", "Targets personal data."),
    ("db_password", "Targets credentials in configuration files."),
    ("aws_access_key_id", "Targets cloud credentials."),
    ("aws_secret_access_key", "Targets cloud credentials."),
    ("begin rsa private key", "Targets private key material."),
    ("begin dsa private key", "Targets private key material."),
    ("begin ec private key", "Targets private key material."),
    ("begin openssh private key", "Targets private key material."),
    (".env", "Targets sensitive environment configuration files."),
    ("wp-config.php", "Targets sensitive configuration files."),
    ("configuration.php", "Targets sensitive configuration files."),
    ("settings.php", "Targets sensitive configuration files."),
    ("database.yml", "Targets sensitive configuration files."),
    ("database.sql", "Targets database dump files."),
    ("mysqldump", "Targets database dump files."),
    ("mail_password", "Targets credentials in configuration files."),
    ("redis_password", "Targets credentials in configuration files."),
    ("stripe_", "Targets payment or secret material."),
    ("paypal_", "Targets payment or secret material."),
    ("twilio_", "Targets secret material."),
    ("github_token", "Targets credentials in configuration files."),
    ("slack_token", "Targets credentials in configuration files."),
    ("telegram_bot_token", "Targets credentials in configuration files."),
    ("id_rsa", "Targets private key material."),
    (".htpasswd", "Targets credential files."),
    ("shadow", "Targets credential files."),
    ("passwd", "Targets credential files."),
    (".git", "Targets repository internals and sensitive artifacts."),
    (".svn", "Targets repository internals and sensitive artifacts."),
    (".ds_store", "Targets application internals rather than safe public recon."),
    ("site:pastebin.com", "Targets third-party paste sites often used for sensitive content."),
    ("site:trello.com", "Targets third-party collaboration content that may contain sensitive data."),
    ("site:docs.google.com", "Targets third-party document hosting that may contain sensitive data."),
    ("/wp-json/wp/v2/users", "Targets user enumeration endpoints."),
)

_SAFE_PARAMETER_TOKENS = (
    "?page=",
    "?search=",
    "?q=",
    "?keyword=",
    "?query=",
    "?view=",
    "?cat=",
    "?pid=",
    "?product_id=",
    "?item=",
)

_SAFE_SERVER_TERMS = (
    "apache http server",
    "welcome to nginx",
    "iis windows server",
    "test page for the apache",
    "apache2 ubuntu default page",
    "openssl",
    "grafana",
    "jenkins",
    "solr/admin",
    "kibana",
    "jupyter",
    "portainer",
    "tomcat",
    "webmin",
    "dashboard",
)

_SAFE_REMOTE_ACCESS_TERMS = (
    "vpn login",
    "cisco vpn",
    "pulse secure",
    "fortinet vpn",
    "globalprotect",
    "anyconnect",
    "fortigate",
    "remote desktop",
    "ssl-vpn",
)

_SAFE_DIRECTORY_TERMS = (
    "backup",
    "uploads",
    "logs",
    "wwwroot",
    "htdocs",
    "src",
    "source",
    "parent directory",
)

_SAFE_FILE_DISCOVERY_TERMS = (
    "filetype:pdf",
    "filetype:xlsx",
    "filetype:doc",
    "filetype:docx",
    "filetype:log",
    "filetype:txt",
)

_STOPWORDS = {
    "site",
    "inurl",
    "intitle",
    "intext",
    "allintitle",
    "allinurl",
    "allintext",
    "filetype",
    "ext",
    "or",
    "and",
    "not",
    "www",
    "http",
    "https",
    "com",
    "php",
    "index",
    "of",
    "domain",
    "example",
}


class TechniqueCollectionImporter:
    """Convert large text-based dork collections into safe structured technique packs."""

    def import_file(
        self,
        source_path: Path,
        output_dir: Path,
        *,
        report_path: Path | None = None,
    ) -> TechniqueImportReport:
        raw_entries = self._parse_source_file(source_path)
        categorized_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
        seen_signatures: dict[tuple[str, str, str], str] = {}
        report = TechniqueImportReport(
            source_file=str(source_path),
            output_dir=str(output_dir),
        )

        for raw_entry in raw_entries:
            converted = self._convert_entry(raw_entry, report)
            if converted is None:
                continue

            technique = converted.payload
            signature = (
                converted.file_name,
                technique["engine"].strip().lower(),
                technique["query_template"].strip().lower(),
            )
            previous_id = seen_signatures.get(signature)
            if previous_id is not None:
                report.exclusions.append(
                    ImportExclusion(
                        line_number=raw_entry.line_number,
                        section_title=raw_entry.section_title,
                        subsection_title=raw_entry.subsection_title,
                        raw_query=raw_entry.raw_query,
                        reason=(
                            "Skipped because it normalizes to a duplicate query template already "
                            f"imported as '{previous_id}'."
                        ),
                    )
                )
                continue

            seen_signatures[signature] = technique["id"]
            categorized_records[converted.file_name].append(technique)

        output_dir.mkdir(parents=True, exist_ok=True)
        for spec in _CATEGORY_SPECS.values():
            techniques = categorized_records.get(spec.file_name, [])
            if not techniques:
                continue

            payload = {
                "category_id": spec.category_id,
                "category_name": spec.category_name,
                "description": spec.description,
                "display_order": spec.display_order,
                "techniques": sorted(techniques, key=lambda item: item["name"].lower()),
            }
            output_path = output_dir / spec.file_name
            output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            report.imported_by_file[spec.file_name] = len(techniques)

        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(self.render_report(report), encoding="utf-8")

        return report

    def render_report(self, report: TechniqueImportReport) -> str:
        reason_counts = Counter(exclusion.reason for exclusion in report.exclusions)
        lines = [
            "# INSANE PK Import Report",
            "",
            f"- Source: `{report.source_file}`",
            f"- Output directory: `{report.output_dir}`",
            f"- Imported techniques: `{report.imported_count}`",
            f"- Excluded lines: `{len(report.exclusions)}`",
            "",
            "## Imported Files",
            "",
        ]

        if report.imported_by_file:
            for file_name, count in sorted(report.imported_by_file.items()):
                lines.append(f"- `{file_name}`: {count} technique(s)")
        else:
            lines.append("- No technique files were generated.")

        lines.extend(["", "## Exclusion Summary", ""])
        if reason_counts:
            for reason, count in reason_counts.most_common():
                lines.append(f"- {count} line(s): {reason}")
        else:
            lines.append("- No lines were excluded.")

        lines.extend(["", "## Sample Exclusions", ""])
        for exclusion in report.exclusions[:20]:
            subsection = f" / {exclusion.subsection_title}" if exclusion.subsection_title else ""
            lines.append(
                f"- Line {exclusion.line_number} [{exclusion.section_title}{subsection}]: "
                f"`{exclusion.raw_query}`"
            )
            lines.append(f"  Reason: {exclusion.reason}")
        if not report.exclusions:
            lines.append("- No sample exclusions to report.")

        lines.append("")
        return "\n".join(lines)

    def _parse_source_file(self, source_path: Path) -> list[RawCollectionEntry]:
        entries: list[RawCollectionEntry] = []
        section_number = 0
        section_title = ""
        subsection_title = ""

        for line_number, raw_line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line or _DECORATION_RE.match(line):
                continue

            section_match = _SECTION_RE.match(line)
            if section_match is not None:
                section_number = int(section_match.group("number"))
                section_title = section_match.group("title").strip().upper()
                subsection_title = ""
                continue

            subsection_match = _SUBSECTION_RE.match(line)
            if subsection_match is not None:
                subsection_title = subsection_match.group("title").strip()
                continue

            if not section_title:
                continue

            if line.startswith("OPERATOR") or line.startswith("-----------"):
                continue
            if line.startswith("Team insane pk official"):
                continue
            if line.startswith("Salam Alikkam"):
                continue

            entries.append(
                RawCollectionEntry(
                    line_number=line_number,
                    section_number=section_number,
                    section_title=section_title,
                    subsection_title=subsection_title,
                    raw_query=line,
                )
            )
        return entries

    def _convert_entry(
        self,
        raw_entry: RawCollectionEntry,
        report: TechniqueImportReport,
    ) -> ImportedTechniqueRecord | None:
        whole_section_reason = _WHOLE_SECTION_EXCLUSIONS.get(raw_entry.section_title)
        if whole_section_reason is not None:
            report.exclusions.append(
                ImportExclusion(
                    line_number=raw_entry.line_number,
                    section_title=raw_entry.section_title,
                    subsection_title=raw_entry.subsection_title,
                    raw_query=raw_entry.raw_query,
                    reason=whole_section_reason,
                )
            )
            return None

        exclusion_reason = self._exclude_query(raw_entry)
        if exclusion_reason is not None:
            report.exclusions.append(
                ImportExclusion(
                    line_number=raw_entry.line_number,
                    section_title=raw_entry.section_title,
                    subsection_title=raw_entry.subsection_title,
                    raw_query=raw_entry.raw_query,
                    reason=exclusion_reason,
                )
            )
            return None

        category_key = self._category_key_for_entry(raw_entry)
        if category_key is None:
            report.exclusions.append(
                ImportExclusion(
                    line_number=raw_entry.line_number,
                    section_title=raw_entry.section_title,
                    subsection_title=raw_entry.subsection_title,
                    raw_query=raw_entry.raw_query,
                    reason="Skipped because the line does not map to a supported safe technique pack.",
                )
            )
            return None

        spec = _CATEGORY_SPECS[category_key]
        query_template = self._normalize_query(raw_entry.raw_query, category_key=category_key)
        variables = self._variables_for_query(query_template)
        example = self._build_example(query_template)
        name = self._build_name(query_template, raw_entry)
        description = self._build_description(name, query_template, raw_entry, spec.category_name)
        tags = self._infer_tags(query_template, raw_entry, category_key)
        technique_id = self._build_id(spec.category_id, query_template)

        payload: dict[str, Any] = {
            "id": technique_id,
            "name": name,
            "category": spec.category_name,
            "engine": spec.engine,
            "description": description,
            "query_template": query_template,
            "variables": variables,
            "tags": tags,
            "example": example,
            "safe_mode": True,
            "reference": spec.reference,
            "launch_url": spec.launch_url,
        }

        return ImportedTechniqueRecord(file_name=spec.file_name, payload=payload)

    def _exclude_query(self, raw_entry: RawCollectionEntry) -> str | None:
        normalized_query = raw_entry.raw_query.lower()

        for blocked_substring, reason in _BLOCKED_SUBSTRINGS:
            if blocked_substring in normalized_query:
                return reason

        section_title = raw_entry.section_title
        if section_title == "EXPOSED DATABASES & CONFIG FILES":
            return (
                "Excluded because the section focuses on database dumps and configuration files "
                "that commonly contain secrets or private operational data."
            )

        if section_title == "CLOUD & STORAGE MISCONFIGURATIONS":
            return (
                "Excluded from automatic import because the section is mostly generic provider-wide "
                "file hunting without a safe target-scoped placeholder."
            )

        if section_title == "FILE & DOCUMENT DISCOVERY":
            if not any(term in normalized_query for term in _SAFE_FILE_DISCOVERY_TERMS):
                return "Skipped because the file discovery line falls outside the allowed safe document and log patterns."

        if section_title == "DIRECTORY LISTINGS":
            if not any(term in normalized_query for term in _SAFE_DIRECTORY_TERMS):
                return "Skipped because the directory listing line targets sensitive or high-risk content."

        if section_title == "VULNERABLE PAGES & PARAMETERS":
            if not any(token in normalized_query for token in _SAFE_PARAMETER_TOKENS):
                return "Skipped because the parameter pattern is too exploit-oriented for the built-in recon catalog."

        if section_title == "SERVER & NETWORK INFO":
            if not any(term in normalized_query for term in _SAFE_SERVER_TERMS):
                return "Skipped because the server discovery line targets raw services or device interfaces outside the safe import scope."

        if section_title == "ERROR MESSAGES & INFO LEAKAGE":
            if "login failed for user" in normalized_query or "access denied for user" in normalized_query:
                return "Skipped because the line is too focused on authentication failure data."

        if section_title == "CMS SPECIFIC DORKS":
            blocked_cms_terms = (
                "/wp-json/wp/v2/users",
                "/wp-content/debug.log",
                "/configuration.php-dist",
                "/app/etc/local.xml",
                "/storage/logs/laravel.log",
                "/_debugbar",
                "csrf verification failed",
            )
            for blocked_term in blocked_cms_terms:
                if blocked_term in normalized_query:
                    return "Skipped because the CMS line points to sensitive debug, user-enumeration, or configuration material."

        if section_title == "VPN, FTP & REMOTE ACCESS":
            if not any(term in normalized_query for term in _SAFE_REMOTE_ACCESS_TERMS):
                return "Skipped because the remote-access line is not a safe target-scoped web login discovery query."

        if section_title == "BUG BOUNTY FOCUSED DORKS":
            blocked_bug_bounty_terms = (
                "filetype:env",
                "filetype:log",
                "filetype:sql",
                "filetype:config",
                "ext:bak",
                "ext:old",
                "ext:swp",
                "ext:tmp",
                'inurl:".git"',
                'inurl:"phpinfo.php"',
                'inurl:"info.php"',
                "inurl:debug",
            )
            for blocked_term in blocked_bug_bounty_terms:
                if blocked_term in normalized_query:
                    return "Skipped because the bug bounty line targets sensitive file exposures or debug artifacts."

        if section_title == "USEFUL DORK COMBINATIONS":
            if "password" in normalized_query or "api_key" in normalized_query:
                return "Skipped because the combination explicitly targets credentials or secrets."

        return None

    def _category_key_for_entry(self, raw_entry: RawCollectionEntry) -> str | None:
        lower_query = raw_entry.raw_query.lower()
        section_title = raw_entry.section_title

        if section_title == "CMS SPECIFIC DORKS":
            return "cms_queries"
        if section_title == "FILE & DOCUMENT DISCOVERY":
            return "exposed_files"
        if section_title == "DIRECTORY LISTINGS":
            return "exposed_files"
        if section_title == "BUG BOUNTY FOCUSED DORKS":
            if any(token in lower_query for token in ("inurl:api", "inurl:v1", "inurl:v2", "inurl:swagger", "inurl:graphql")):
                return "api_discovery"
            return "google_dorks"
        if section_title == "USEFUL DORK COMBINATIONS":
            if any(token in lower_query for token in ("wp-json", "api", "swagger", "graphql")):
                return "api_discovery"
            return "google_dorks"
        if section_title in {
            "LOGIN & ADMIN PANELS",
            "VULNERABLE PAGES & PARAMETERS",
            "SERVER & NETWORK INFO",
            "ERROR MESSAGES & INFO LEAKAGE",
            "VPN, FTP & REMOTE ACCESS",
        }:
            return "google_dorks"
        return None

    def _normalize_query(self, raw_query: str, *, category_key: str) -> str:
        query = _WHITESPACE_RE.sub(" ", raw_query.strip())
        query = _EXAMPLE_DOMAIN_RE.sub("{domain}", query)

        if category_key in {"google_dorks", "api_discovery", "exposed_files", "cms_queries"}:
            if "{domain}" not in query and not query.startswith("site:"):
                query = f"site:{{domain}} {query}"
        return query

    def _variables_for_query(self, query_template: str) -> list[dict[str, Any]]:
        variable_examples = {
            "domain": ("Primary authorized target domain or hostname.", "example.com"),
            "company": ("Target company or organization name.", "Example Corp"),
            "keyword": ("Target keyword, product, or brand string.", "customer portal"),
            "org": ("Organization or business unit identifier.", "example-org"),
        }
        variables: list[dict[str, Any]] = []
        for variable_name in sorted({match.group("name") for match in _VARIABLE_RE.finditer(query_template)}):
            description, example = variable_examples.get(
                variable_name,
                ("Target-specific value used when rendering the query.", "example"),
            )
            variables.append(
                {
                    "name": variable_name,
                    "description": description,
                    "required": True,
                    "example": example,
                }
            )
        return variables

    def _build_example(self, query_template: str) -> str:
        replacements = {
            "domain": "example.com",
            "company": "Example Corp",
            "keyword": "customer portal",
            "org": "example-org",
        }
        return query_template.format(**replacements)

    def _build_name(self, query_template: str, raw_entry: RawCollectionEntry) -> str:
        lower_query = query_template.lower()
        subsection = raw_entry.subsection_title

        matcher_names: tuple[tuple[tuple[str, ...], str], ...] = (
            (("swagger", "openapi"), "Swagger and OpenAPI Search"),
            (("graphql",), "GraphQL Surface Search"),
            (("robots.txt",), "Robots.txt Discovery"),
            (("sitemap.xml",), "Sitemap Discovery"),
            (("wp-admin",), "WordPress Admin Search"),
            (("wp-login.php",), "WordPress Login Search"),
            (("wp-content/uploads",), "WordPress Uploads Search"),
            (("wp-includes",), "WordPress Includes Search"),
            (("xml-rpc", "xmlrpc.php"), "WordPress XML-RPC Search"),
            (("/administrator/index.php",), "Joomla Admin Search"),
            (("joomla",), "Joomla Surface Search"),
            (("drupal", "/user/login", "/?q=user/login"), "Drupal Surface Search"),
            (("magento", "/downloader/"), "Magento Surface Search"),
            (("django site admin",), "Django Admin Search"),
            (("django version",), "Django Version Disclosure Search"),
            (("admin login",), "Admin Login Search"),
            (("login", "signin"), "Login Surface Search"),
            (("dashboard", "control panel", "admin panel", "portal"), "Admin Surface Search"),
            (('intitle:"index of"', "backup"), "Backup Directory Listing Search"),
            (('intitle:"index of"', "uploads"), "Uploads Directory Listing Search"),
            (('intitle:"index of"', "logs"), "Log Directory Listing Search"),
            (('intitle:"index of"',), "Directory Listing Search"),
            (("apache http server", "apache2 ubuntu default page", "welcome to nginx", "iis windows server"), "Default Server Page Search"),
            (("grafana",), "Grafana Interface Search"),
            (("jenkins",), "Jenkins Interface Search"),
            (("jupyter",), "Jupyter Interface Search"),
            (("kibana",), "Kibana Interface Search"),
            (("elasticsearch",), "Elasticsearch Interface Search"),
            (("portainer",), "Portainer Interface Search"),
            (("webmin",), "Webmin Interface Search"),
            (("tomcat",), "Tomcat Manager Search"),
            (("manager/html",), "Tomcat Manager Search"),
            (("vpn login", "cisco vpn", "pulse secure", "fortinet vpn", "globalprotect", "anyconnect", "fortigate", "ssl-vpn"), "VPN Portal Search"),
            (("remote desktop",), "Remote Desktop Web Search"),
            (("traceback", "stack trace", "exception", "php fatal error", "php warning", "php parse error"), "Error Disclosure Search"),
            (("?page=", "?search=", "?q=", "?keyword=", "?query=", "?view="), "Indexed Parameter Search"),
            (("?product_id=", "?item=", "?cat=", "?pid="), "Indexed Catalog Parameter Search"),
            (("filetype:pdf",), "Public PDF Search"),
            (("filetype:docx",), "Public DOCX Search"),
            (("filetype:doc",), "Public DOC Search"),
            (("filetype:xlsx",), "Public Spreadsheet Search"),
            (("filetype:log",), "Log File Search"),
            (("inurl:api",), "API Path Search"),
            (("inurl:v1",), "Versioned API v1 Search"),
            (("inurl:v2",), "Versioned API v2 Search"),
            (("inurl:dev", "inurl:staging", "inurl:beta", "inurl:test"), "Environment Surface Search"),
            (("inurl:backup",), "Backup Surface Search"),
            (("inurl:admin",), "Admin Surface Search"),
            (("inurl:upload",), "Upload Surface Search"),
            (("inurl:download",), "Download Surface Search"),
        )
        for needles, name in matcher_names:
            if all(needle in lower_query for needle in needles):
                return name
            if len(needles) == 1 and needles[0] in lower_query:
                return name

        if subsection:
            return f"{subsection.strip()} Surface Search"
        return self._fallback_name(query_template)

    def _build_description(
        self,
        name: str,
        query_template: str,
        raw_entry: RawCollectionEntry,
        category_name: str,
    ) -> str:
        lower_query = query_template.lower()
        if category_name == "Exposed Files":
            return (
                f"Searches indexed content on a target domain for {self._describe_focus(lower_query)}. "
                "This helps identify public files, directory listings, or document collections that support authorized recon."
            )
        if category_name == "CMS Queries":
            cms_name = raw_entry.subsection_title or "CMS"
            return (
                f"Searches a target domain for {self._describe_focus(lower_query)} associated with {cms_name}. "
                "This is useful for spotting public CMS components, admin surfaces, and implementation clues."
            )
        if category_name == "API Discovery":
            return (
                f"Searches a target domain for {self._describe_focus(lower_query)}. "
                "This supports discovery of public API routes, versioned endpoints, and developer-facing materials."
            )
        return (
            f"Searches indexed pages on a target domain for {self._describe_focus(lower_query)}. "
            "This is useful for admin surface mapping, technology discovery, and public recon on authorized targets."
        )

    def _describe_focus(self, lower_query: str) -> str:
        if "swagger" in lower_query or "openapi" in lower_query:
            return "Swagger or OpenAPI references"
        if "graphql" in lower_query:
            return "GraphQL routes and related references"
        if "robots.txt" in lower_query:
            return "robots.txt files"
        if "sitemap.xml" in lower_query:
            return "sitemap files"
        if 'intitle:"index of"' in lower_query:
            return "directory listing pages"
        if "login" in lower_query or "signin" in lower_query:
            return "login and authentication surfaces"
        if "admin" in lower_query or "dashboard" in lower_query or "portal" in lower_query:
            return "admin-facing pages and dashboards"
        if "traceback" in lower_query or "exception" in lower_query or "error" in lower_query:
            return "error messages and framework leakage"
        if "filetype:pdf" in lower_query:
            return "public PDF documents"
        if "filetype:docx" in lower_query or "filetype:doc" in lower_query:
            return "public office documents"
        if "filetype:xlsx" in lower_query:
            return "public spreadsheets and exported reports"
        if "filetype:log" in lower_query:
            return "public log or debug text files"
        if "wp-" in lower_query or "wordpress" in lower_query:
            return "WordPress assets and public endpoints"
        if "joomla" in lower_query:
            return "Joomla entry points and public components"
        if "drupal" in lower_query:
            return "Drupal login and routing surfaces"
        if "magento" in lower_query:
            return "Magento administration and support surfaces"
        if "django" in lower_query:
            return "Django administrative and versioning clues"
        if "vpn" in lower_query or "remote" in lower_query:
            return "remote access portals"
        return "publicly indexed recon-relevant pages"

    def _infer_tags(
        self,
        query_template: str,
        raw_entry: RawCollectionEntry,
        category_key: str,
    ) -> list[str]:
        tags: list[str] = []
        if category_key == "google_dorks":
            tags.extend(["google", "recon"])
        elif category_key == "api_discovery":
            tags.extend(["google", "api", "recon"])
        elif category_key == "exposed_files":
            tags.extend(["google", "files", "recon"])
        elif category_key == "cms_queries":
            tags.extend(["google", "cms", "recon"])

        lower_query = query_template.lower()
        tag_rules: tuple[tuple[str, str], ...] = (
            ("login", "authentication"),
            ("signin", "authentication"),
            ("admin", "admin-surface"),
            ("dashboard", "dashboards"),
            ("portal", "dashboards"),
            ("swagger", "openapi"),
            ("openapi", "openapi"),
            ("graphql", "graphql"),
            ("robots.txt", "robots-txt"),
            ("sitemap.xml", "sitemaps"),
            ('intitle:"index of"', "directory-listing"),
            ("filetype:pdf", "documents"),
            ("filetype:doc", "documents"),
            ("filetype:docx", "documents"),
            ("filetype:xlsx", "spreadsheets"),
            ("filetype:log", "logs"),
            ("traceback", "error-pages"),
            ("exception", "error-pages"),
            ("wp-", "wordpress"),
            ("joomla", "joomla"),
            ("drupal", "drupal"),
            ("magento", "magento"),
            ("django", "django"),
            ("laravel", "laravel"),
            ("vpn", "remote-access"),
            ("remote desktop", "remote-access"),
            ("api", "api-discovery"),
            ("inurl:v1", "versioning"),
            ("inurl:v2", "versioning"),
            ("inurl:dev", "environments"),
            ("inurl:staging", "environments"),
            ("inurl:beta", "environments"),
            ("inurl:test", "environments"),
        )
        for needle, tag in tag_rules:
            if needle in lower_query:
                tags.append(tag)

        if raw_entry.subsection_title:
            tags.append(_slugify(raw_entry.subsection_title))

        deduped: list[str] = []
        for tag in tags:
            normalized = tag.strip().lower()
            if normalized and normalized not in deduped:
                deduped.append(normalized)
        return deduped[:6]

    def _build_id(self, category_id: str, query_template: str) -> str:
        digest = hashlib.sha1(query_template.strip().lower().encode("utf-8")).hexdigest()[:8]
        candidate_tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", query_template.lower())
            if token not in _STOPWORDS
        ]
        slug = "-".join(candidate_tokens[:6]) or "query"
        prefix = category_id.removesuffix("_queries").removesuffix("_dorks")
        return f"{prefix}-{slug}-{digest}"

    def _fallback_name(self, query_template: str) -> str:
        tokens = [
            token
            for token in re.findall(r"[A-Za-z0-9]+", query_template)
            if token.lower() not in _STOPWORDS and token.lower() != "domain"
        ]
        if not tokens:
            return "Search Technique"
        return " ".join(token.capitalize() for token in tokens[:4]) + " Search"


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = _NON_ALNUM_RE.sub("-", lowered).strip("-")
    return slug or "value"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import a large text collection into DorkVault technique packs."
    )
    parser.add_argument("source_file", type=Path, help="Path to the source text collection.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where generated technique pack JSON files should be written.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path for a markdown import report.",
    )
    args = parser.parse_args(argv)

    importer = TechniqueCollectionImporter()
    report = importer.import_file(
        args.source_file,
        args.output_dir,
        report_path=args.report,
    )

    print(
        f"Imported {report.imported_count} technique(s) into "
        f"{len(report.imported_by_file)} file(s); excluded {len(report.exclusions)} line(s)."
    )
    for file_name, count in sorted(report.imported_by_file.items()):
        print(f"- {file_name}: {count}")
    if args.report is not None:
        print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
