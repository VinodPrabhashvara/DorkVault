"""Shared metadata for bundled technique packs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TechniquePackSpec:
    """Static metadata for one bundled technique pack."""

    pack_key: str
    file_name: str
    category_id: str
    category_name: str
    description: str
    display_order: int
    engine: str
    reference: str
    launch_url: str


PACK_SPECS: dict[str, TechniquePackSpec] = {
    "google_dorks": TechniquePackSpec(
        pack_key="google_dorks",
        file_name="google_dorks.json",
        category_id="google_dorks",
        category_name="Google Dorks",
        description=(
            "Target-scoped Google search techniques for public asset discovery, "
            "admin surface mapping, technology fingerprinting, documentation search, "
            "and public error leakage review."
        ),
        display_order=10,
        engine="Google",
        reference="https://support.google.com/websearch/answer/2466433",
        launch_url="https://www.google.com/search?q={query}",
    ),
    "github_queries": TechniquePackSpec(
        pack_key="github_queries",
        file_name="github_queries.json",
        category_id="github_queries",
        category_name="GitHub Search",
        description=(
            "Public GitHub search queries for finding documentation, workflows, "
            "deployment clues, and code references tied to a target."
        ),
        display_order=20,
        engine="GitHub",
        reference=(
            "https://docs.github.com/en/search-github/"
            "github-code-search/understanding-github-code-search-syntax"
        ),
        launch_url="https://github.com/search?q={query}&type=code",
    ),
    "wayback_queries": TechniquePackSpec(
        pack_key="wayback_queries",
        file_name="wayback_queries.json",
        category_id="wayback_queries",
        category_name="Wayback",
        description=(
            "Archive lookups for historical content, routes, scripts, and endpoints "
            "visible in the Wayback Machine."
        ),
        display_order=30,
        engine="Wayback Machine",
        reference="https://web.archive.org/",
        launch_url="https://web.archive.org/web/*/{domain}/*",
    ),
    "shodan_queries": TechniquePackSpec(
        pack_key="shodan_queries",
        file_name="shodan_queries.json",
        category_id="shodan_queries",
        category_name="Shodan",
        description="Search queries for reviewing internet-facing services indexed by Shodan.",
        display_order=40,
        engine="Shodan",
        reference="https://help.shodan.io/the-basics/search-query-fundamentals",
        launch_url="https://www.shodan.io/search?query={query}",
    ),
    "censys_queries": TechniquePackSpec(
        pack_key="censys_queries",
        file_name="censys_queries.json",
        category_id="censys_queries",
        category_name="Censys",
        description="Search queries for reviewing hosts and certificate-related data indexed in Censys.",
        display_order=50,
        engine="Censys",
        reference="https://search.censys.io/help",
        launch_url="https://search.censys.io/search?resource=hosts&q={query}",
    ),
    "cloud_storage": TechniquePackSpec(
        pack_key="cloud_storage",
        file_name="cloud_storage.json",
        category_id="cloud_storage",
        category_name="Cloud Storage",
        description=(
            "Search-based recon queries for public cloud storage references associated "
            "with a company, brand, keyword, or target domain."
        ),
        display_order=60,
        engine="Google",
        reference="https://support.google.com/websearch/answer/2466433",
        launch_url="https://www.google.com/search?q={query}",
    ),
    "cms_queries": TechniquePackSpec(
        pack_key="cms_queries",
        file_name="cms_queries.json",
        category_id="cms_queries",
        category_name="CMS Queries",
        description=(
            "Search queries for discovering public WordPress, Joomla, Drupal, Magento, "
            "Laravel, Django, Ghost, and Strapi surfaces on authorized targets."
        ),
        display_order=70,
        engine="Google",
        reference="https://support.google.com/websearch/answer/2466433",
        launch_url="https://www.google.com/search?q={query}",
    ),
    "api_discovery": TechniquePackSpec(
        pack_key="api_discovery",
        file_name="api_discovery.json",
        category_id="api_discovery",
        category_name="API Discovery",
        description=(
            "Search engine techniques for finding public API routes, developer "
            "documentation, schema files, versioned endpoints, and integration clues."
        ),
        display_order=80,
        engine="Google",
        reference="https://support.google.com/websearch/answer/2466433",
        launch_url="https://www.google.com/search?q={query}",
    ),
    "ct_logs": TechniquePackSpec(
        pack_key="ct_logs",
        file_name="ct_logs.json",
        category_id="ct_logs",
        category_name="CT Logs",
        description=(
            "Certificate Transparency lookup queries for reviewing public certificate "
            "metadata related to a target domain or organization."
        ),
        display_order=90,
        engine="crt.sh",
        reference="https://crt.sh/",
        launch_url="https://crt.sh/?q={domain}",
    ),
    "exposed_files": TechniquePackSpec(
        pack_key="exposed_files",
        file_name="exposed_files.json",
        category_id="exposed_files",
        category_name="Exposed Files",
        description=(
            "Target-scoped file and directory discovery searches for public documents, "
            "logs, backups, exports, and browsable directory listings."
        ),
        display_order=100,
        engine="Google",
        reference="https://support.google.com/websearch/answer/2466433",
        launch_url="https://www.google.com/search?q={query}",
    ),
}


PACK_KEYS = tuple(PACK_SPECS)
CATEGORY_NAMES = {spec.category_name for spec in PACK_SPECS.values()}
ENGINE_NAMES = {spec.engine for spec in PACK_SPECS.values()}


VARIABLE_LIBRARY: dict[str, dict[str, object]] = {
    "domain": {
        "name": "domain",
        "description": "Primary target domain or hostname.",
        "required": True,
        "example": "example.com",
    },
    "company": {
        "name": "company",
        "description": "Target company or organization name.",
        "required": True,
        "example": "Example Corp",
    },
    "keyword": {
        "name": "keyword",
        "description": "Target keyword, product, or free-text phrase.",
        "required": True,
        "example": "customer portal",
    },
    "org": {
        "name": "org",
        "description": "Organization or team identifier.",
        "required": True,
        "example": "example-org",
    },
}
