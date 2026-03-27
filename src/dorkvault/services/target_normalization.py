"""Helpers for normalizing user-entered target values."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(slots=True, frozen=True)
class TargetNormalizationResult:
    """Describe how a target value was normalized for a technique variable."""

    original_value: str
    normalized_value: str
    variable_name: str

    @property
    def was_normalized(self) -> bool:
        return self.normalized_value != self.original_value

    @property
    def helper_text(self) -> str:
        if self.variable_name == "domain" and self.was_normalized:
            return f"Using normalized domain: {self.normalized_value}"
        return ""


def normalize_target_input(target_input: str, *, variable_name: str = "") -> TargetNormalizationResult:
    """Normalize a target value when a technique variable expects a domain."""
    cleaned_value = target_input.strip()
    normalized_variable_name = variable_name.strip().lower()
    normalized_value = cleaned_value

    if normalized_variable_name == "domain":
        normalized_value = normalize_domain_target(cleaned_value)

    return TargetNormalizationResult(
        original_value=cleaned_value,
        normalized_value=normalized_value,
        variable_name=normalized_variable_name,
    )


def normalize_domain_target(target_input: str) -> str:
    """Extract the hostname from URL-like input while preserving plain domains."""
    cleaned_value = target_input.strip()
    if not cleaned_value:
        return ""

    trimmed_value = cleaned_value.rstrip("/")
    parsed_hostname = _extract_hostname_from_url_like_value(trimmed_value)
    return parsed_hostname or trimmed_value


def _extract_hostname_from_url_like_value(value: str) -> str:
    if any(character.isspace() for character in value):
        return ""

    if "://" in value:
        return _hostname_from_split(urlsplit(value))

    if value.startswith("//"):
        return _hostname_from_split(urlsplit(f"http:{value}"))

    if any(separator in value for separator in ("/", "?", "#")):
        return _hostname_from_split(urlsplit(f"//{value}"))

    return ""


def _hostname_from_split(parsed_value) -> str:  # noqa: ANN001
    host = parsed_value.netloc.strip()
    if not host:
        return ""

    host = host.rsplit("@", 1)[-1]
    if host.startswith("["):
        closing_index = host.find("]")
        if closing_index != -1:
            return host[1:closing_index]

    if host.count(":") == 1:
        host = host.split(":", 1)[0]

    return host.rstrip("/")
