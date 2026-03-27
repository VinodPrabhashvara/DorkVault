"""Shared normalization helpers for catalog generation and validation."""

from __future__ import annotations

import re

_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SMART_QUOTES = str.maketrans(
    {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "`": "'",
    }
)
_SIGNATURE_STOPWORDS = {
    "site",
    "inurl",
    "intitle",
    "intext",
    "allintitle",
    "allinurl",
    "allintext",
    "filetype",
    "filename",
    "path",
    "http",
    "https",
    "or",
    "and",
    "not",
    "domain",
    "company",
    "keyword",
    "org",
    "raw",
}


def normalize_template(query_template: str) -> str:
    """Normalize a query template for duplicate detection."""
    normalized = query_template.translate(_SMART_QUOTES).strip()
    normalized = _SPACE_RE.sub(" ", normalized)
    normalized = normalized.replace(" : ", ":").replace(": ", ":").replace(" :", ":")
    return normalized


def normalized_template_signature(engine: str, query_template: str) -> tuple[str, str]:
    """Return a strict duplicate signature for a technique template."""
    return (
        engine.strip().lower(),
        normalize_template(query_template).lower(),
    )


def near_duplicate_signature(engine: str, query_template: str) -> tuple[str, tuple[str, ...]]:
    """Return a looser intent signature used for near-duplicate detection."""
    normalized_template = normalize_template(query_template).lower()
    normalized_template = normalized_template.replace('"', " ").replace("'", " ")
    normalized_template = normalized_template.replace("{", " ").replace("}", " ")
    normalized_template = normalized_template.replace("(", " ").replace(")", " ")
    normalized_template = normalized_template.replace("[", " ").replace("]", " ")
    normalized_template = normalized_template.replace(",", " ").replace(":", " ")
    tokens = [
        token
        for token in _TOKEN_RE.findall(normalized_template)
        if token not in _SIGNATURE_STOPWORDS
    ]
    return (
        engine.strip().lower(),
        tuple(sorted(dict.fromkeys(tokens))),
    )


def normalize_name(name: str) -> str:
    """Normalize a human-readable technique name for duplicate detection."""
    return normalize_template(name).lower()
