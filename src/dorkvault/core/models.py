"""Dataclass models used across the application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping
from urllib.parse import quote_plus

from dorkvault.core.constants import (
    BROWSER_BEHAVIOR_OPTIONS,
    DEFAULT_BROWSER_BEHAVIOR,
    DEFAULT_RECENT_LIMIT,
    DEFAULT_THEME,
    MAX_RECENT_LIMIT,
    MIN_RECENT_LIMIT,
    THEME_OPTIONS,
)
from dorkvault.core.exceptions import MalformedTemplateError

_VARIABLE_NAME_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"


def _is_valid_variable_name(value: str) -> bool:
    if not value or value[0].isdigit():
        return False
    return all(character in _VARIABLE_NAME_CHARS for character in value)


def _normalize_window_geometry(
    payload: Mapping[str, Any] | None,
) -> dict[str, int] | None:
    if not isinstance(payload, Mapping):
        return None

    normalized: dict[str, int] = {}
    for key in ("x", "y", "width", "height"):
        value = payload.get(key)
        if not isinstance(value, int):
            return None
        normalized[key] = value

    if normalized["width"] <= 0 or normalized["height"] <= 0:
        return None
    return normalized


@dataclass(slots=True, frozen=True)
class TechniqueVariable:
    """A named placeholder used when rendering a technique query."""

    name: str
    description: str = ""
    required: bool = True
    default: str = ""
    example: str = ""

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not _is_valid_variable_name(normalized_name):
            raise ValueError(
                "Technique variable names must be non-empty and use letters, numbers, or underscores."
            )
        if not isinstance(self.required, bool):
            raise ValueError("Technique variable 'required' must be a boolean.")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "default", self.default.strip())
        object.__setattr__(self, "example", self.example.strip())

    @classmethod
    def from_value(cls, payload: str | Mapping[str, Any]) -> TechniqueVariable:
        """Build a variable from shorthand or explicit JSON-style data."""
        if isinstance(payload, str):
            return cls(name=payload)
        if not isinstance(payload, Mapping):
            raise ValueError("Technique variables must be strings or objects.")
        required = payload.get("required", True)
        if not isinstance(required, bool):
            raise ValueError("Technique variable 'required' must be a boolean.")

        return cls(
            name=str(payload.get("name", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            required=required,
            default=str(payload.get("default", "")).strip(),
            example=str(payload.get("example", "")).strip(),
        )


@dataclass(slots=True, frozen=True)
class Technique:
    """A data-driven search or recon technique loaded from JSON."""

    id: str
    name: str
    category: str
    engine: str
    description: str
    query_template: str
    variables: list[TechniqueVariable] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    example: str = ""
    safe_mode: bool = True
    reference: str = ""
    launch_url: str = ""
    source_file: str = ""
    _search_text_cache: str = field(default="", init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        required_fields = (
            "id",
            "name",
            "category",
            "engine",
            "description",
            "query_template",
            "example",
            "reference",
        )
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Technique field '{field_name}' must be a non-empty string.")

        if not isinstance(self.safe_mode, bool):
            raise ValueError("Technique field 'safe_mode' must be a boolean.")

        normalized_tags = tuple(
            sorted(
                {
                    str(tag).strip().lower()
                    for tag in self.tags
                    if isinstance(tag, str) and str(tag).strip()
                }
            )
        )
        object.__setattr__(self, "tags", list(normalized_tags))

        normalized_variables: list[TechniqueVariable] = []
        variable_names: set[str] = set()
        for raw_variable in self.variables:
            variable = (
                raw_variable
                if isinstance(raw_variable, TechniqueVariable)
                else TechniqueVariable.from_value(raw_variable)
            )
            if variable.name in variable_names:
                raise ValueError(f"Duplicate technique variable '{variable.name}'.")
            variable_names.add(variable.name)
            normalized_variables.append(variable)

        object.__setattr__(self, "variables", normalized_variables)
        object.__setattr__(self, "example", self.example.strip())
        object.__setattr__(self, "reference", self.reference.strip())
        object.__setattr__(self, "launch_url", self.launch_url.strip())
        object.__setattr__(self, "source_file", self.source_file.strip())

        try:
            template_variables = self.template_variables
        except MalformedTemplateError as exc:
            raise ValueError(str(exc)) from exc

        missing_variables = template_variables - variable_names
        if missing_variables:
            raise ValueError(
                "Technique query_template references undefined variables: "
                + ", ".join(sorted(missing_variables))
            )

        variable_text = " ".join(variable.name for variable in self.variables)
        object.__setattr__(
            self,
            "_search_text_cache",
            " ".join(
                [
                    self.name,
                    self.category,
                    self.engine,
                    self.description,
                    self.example,
                    self.reference,
                    variable_text,
                    " ".join(self.tags),
                ]
            ).lower(),
        )

    @property
    def template_variables(self) -> set[str]:
        """Return placeholder names referenced by the query template."""
        from dorkvault.services.query_renderer import DEFAULT_QUERY_RENDERER

        return DEFAULT_QUERY_RENDERER.template_variables(self.query_template)

    @property
    def variable_names(self) -> list[str]:
        """Return declared variable names in stable order."""
        return [variable.name for variable in self.variables]

    @property
    def required_variables(self) -> list[TechniqueVariable]:
        """Return variables that must be supplied to render the query."""
        return [variable for variable in self.variables if variable.required]

    @property
    def primary_variable_name(self) -> str | None:
        """Return the best single variable to drive from the main target input."""
        if len(self.required_variables) > 1:
            return None

        variable_names = set(self.variable_names)
        for preferred_name in ("target", "domain", "company", "keyword"):
            if preferred_name in variable_names:
                return preferred_name

        if len(self.required_variables) == 1:
            return self.required_variables[0].name
        if len(self.variables) == 1:
            return self.variables[0].name
        return None

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        default_category: str = "",
        source_file: str = "",
    ) -> Technique:
        """Create a technique from JSON-style data.

        This accepts the current schema and also normalizes legacy starter
        records that still use keys such as `provider`, `target_hint`, and `notes`.
        """
        category = str(payload.get("category") or default_category).strip()
        engine = str(payload.get("engine") or payload.get("provider", "")).strip()
        query_template = str(payload.get("query_template", "")).strip()
        raw_variables = payload.get("variables")
        launch_url = str(payload.get("launch_url", "")).strip()
        reference = str(payload.get("reference", "")).strip()
        notes = str(payload.get("notes", "")).strip()
        target_hint = str(payload.get("target_hint", "")).strip()
        safe_mode = payload.get("safe_mode", True)
        raw_tags = payload.get("tags", [])

        if not isinstance(safe_mode, bool):
            raise ValueError("Technique field 'safe_mode' must be a boolean.")
        if not isinstance(raw_tags, list):
            raise ValueError("Technique field 'tags' must be a list.")

        if raw_variables is None:
            variables = cls._default_variables(query_template=query_template, target_hint=target_hint)
        elif isinstance(raw_variables, list):
            variables = [TechniqueVariable.from_value(item) for item in raw_variables]
        else:
            raise ValueError("Technique field 'variables' must be a list.")

        example = str(payload.get("example", "")).strip()
        if not example and target_hint:
            try:
                example = query_template.format(target=target_hint)
            except Exception:
                example = target_hint

        if not reference:
            reference = launch_url or notes

        return cls(
            id=str(payload.get("id", "")).strip(),
            name=str(payload.get("name", "")).strip(),
            category=category,
            engine=engine,
            description=str(payload.get("description", "")).strip(),
            query_template=query_template,
            variables=variables,
            tags=[str(tag).strip() for tag in raw_tags],
            example=example,
            safe_mode=safe_mode,
            reference=reference,
            launch_url=launch_url,
            source_file=source_file,
        )

    @staticmethod
    def _default_variables(query_template: str, target_hint: str) -> list[TechniqueVariable]:
        if "{target}" not in query_template:
            return []
        return [
            TechniqueVariable(
                name="target",
                description="Primary target value used when rendering the query.",
                required=True,
                example=target_hint,
            )
        ]

    def render_query(self, values: Mapping[str, Any] | None = None) -> str:
        """Render the query using provided variable values."""
        from dorkvault.services.query_renderer import DEFAULT_QUERY_RENDERER

        return DEFAULT_QUERY_RENDERER.render(self, values).query

    def build_variables_from_target_input(self, target_input: str) -> dict[str, str]:
        """Map the single UI target input to the technique's primary variable."""
        cleaned_target = target_input.strip()
        if not cleaned_target:
            raise ValueError("A target value is required to render this technique.")

        primary_variable_name = self.primary_variable_name
        if primary_variable_name is None:
            raise ValueError(
                "This technique requires multiple variables and cannot be rendered from a single target input."
            )

        from dorkvault.services.target_normalization import normalize_target_input

        normalization_result = normalize_target_input(
            cleaned_target,
            variable_name=primary_variable_name,
        )
        return {primary_variable_name: normalization_result.normalized_value}

    def build_query(self, target: str) -> str:
        """Render the query using the main target input field."""
        return self.render_query(self.build_variables_from_target_input(target))

    def build_url(self, target: str) -> str:
        """Build a launchable URL for the rendered query."""
        if not self.launch_url:
            raise ValueError("This technique does not define a launch URL.")

        variable_values = self.build_variables_from_target_input(target)
        rendered_query = self.render_query(variable_values)
        primary_value = next(iter(variable_values.values()))
        format_values: dict[str, str] = {}
        for name, raw_value in variable_values.items():
            format_values[name] = quote_plus(raw_value)
            format_values[f"raw_{name}"] = raw_value

        format_values["query"] = quote_plus(rendered_query)
        format_values["raw_query"] = rendered_query
        format_values["target"] = quote_plus(primary_value)
        format_values["raw_target"] = primary_value
        return self.launch_url.format(
            **format_values,
        )

    def search_text(self) -> str:
        """Return normalized text useful for search indexing and filtering."""
        return self._search_text_cache


@dataclass(slots=True)
class TechniqueCategory:
    """A category grouping multiple techniques."""

    id: str
    name: str
    description: str
    display_order: int = 100
    group_id: str = ""
    group_name: str = ""
    group_description: str = ""
    group_display_order: int = 100
    techniques: list[Technique] = field(default_factory=list)


@dataclass(slots=True)
class TechniqueCategoryGroup:
    """A sidebar-friendly grouping of related categories."""

    id: str
    name: str
    description: str = ""
    display_order: int = 100
    categories: list[TechniqueCategory] = field(default_factory=list)


@dataclass(slots=True)
class AppSettings:
    """Simple local settings persisted as JSON."""

    theme: str = DEFAULT_THEME
    open_in_browser_behavior: str = DEFAULT_BROWSER_BEHAVIOR
    recent_limit: int = DEFAULT_RECENT_LIMIT
    compact_view_enabled: bool = True
    last_target: str = ""
    window_geometry: dict[str, int] | None = None

    def __post_init__(self) -> None:
        normalized_theme = self.theme.strip().lower() or DEFAULT_THEME
        if normalized_theme not in THEME_OPTIONS:
            normalized_theme = DEFAULT_THEME
        self.theme = normalized_theme
        self.last_target = self.last_target.strip()

        normalized_behavior = self.open_in_browser_behavior.strip().lower()
        if normalized_behavior not in BROWSER_BEHAVIOR_OPTIONS:
            raise ValueError(
                "App setting 'open_in_browser_behavior' must be one of: "
                + ", ".join(BROWSER_BEHAVIOR_OPTIONS)
            )
        self.open_in_browser_behavior = normalized_behavior

        if not isinstance(self.compact_view_enabled, bool):
            raise ValueError("App setting 'compact_view_enabled' must be a boolean.")

        if not isinstance(self.recent_limit, int):
            raise ValueError("App setting 'recent_limit' must be an integer.")
        self.recent_limit = max(MIN_RECENT_LIMIT, min(MAX_RECENT_LIMIT, self.recent_limit))
        self.window_geometry = _normalize_window_geometry(self.window_geometry)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AppSettings:
        """Build settings from JSON-style data with safe normalization."""
        theme = str(payload.get("theme", DEFAULT_THEME)).strip().lower() or DEFAULT_THEME
        if theme not in THEME_OPTIONS:
            theme = DEFAULT_THEME

        open_behavior = str(
            payload.get("open_in_browser_behavior", DEFAULT_BROWSER_BEHAVIOR)
        ).strip().lower()
        if open_behavior not in BROWSER_BEHAVIOR_OPTIONS:
            open_behavior = DEFAULT_BROWSER_BEHAVIOR

        raw_recent_limit = payload.get("recent_limit", DEFAULT_RECENT_LIMIT)
        recent_limit = raw_recent_limit if isinstance(raw_recent_limit, int) else DEFAULT_RECENT_LIMIT
        recent_limit = max(MIN_RECENT_LIMIT, min(MAX_RECENT_LIMIT, recent_limit))

        compact_view_enabled = payload.get("compact_view_enabled", True)
        if not isinstance(compact_view_enabled, bool):
            compact_view_enabled = True

        last_target = str(payload.get("last_target", "")).strip()
        window_geometry = _normalize_window_geometry(payload.get("window_geometry"))

        return cls(
            theme=theme,
            open_in_browser_behavior=open_behavior,
            recent_limit=recent_limit,
            compact_view_enabled=compact_view_enabled,
            last_target=last_target,
            window_geometry=window_geometry,
        )
