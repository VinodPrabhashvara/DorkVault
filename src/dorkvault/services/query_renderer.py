"""Render technique queries from templates and user-provided values."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter
from typing import Callable, Mapping

from dorkvault.core.exceptions import MalformedTemplateError, MissingVariableError
from dorkvault.core.models import Technique

EngineRenderHook = Callable[[Technique, str, Mapping[str, str]], str]


@dataclass(slots=True)
class QueryRenderResult:
    """Structured result for a rendered technique query."""

    technique_id: str
    engine: str
    query: str
    variables: dict[str, str]


class QueryRenderer:
    """Render technique templates into final query strings.

    The renderer supports engine-specific post-processing hooks so different
    providers can customize output in the future without changing the Technique model.
    """

    def __init__(self) -> None:
        self._engine_hooks: dict[str, EngineRenderHook] = {}

    def register_engine_hook(self, engine: str, hook: EngineRenderHook) -> None:
        """Register a post-processing hook for a specific engine name."""
        normalized_engine = engine.strip().lower()
        if not normalized_engine:
            raise ValueError("Engine name is required when registering a render hook.")
        self._engine_hooks[normalized_engine] = hook

    def template_variables(self, query_template: str) -> set[str]:
        """Extract placeholder names from a query template."""
        try:
            parsed_fields = Formatter().parse(query_template)
            names = {field_name for _, field_name, _, _ in parsed_fields if field_name}
        except ValueError as exc:
            raise MalformedTemplateError(f"Malformed query template: {exc}") from exc
        return names

    def render(self, technique: Technique, values: Mapping[str, object] | None = None) -> QueryRenderResult:
        """Render a technique into its final query string."""
        normalized_values = self._normalize_values(values or {})
        prepared_values = self._prepare_values(technique=technique, values=normalized_values)

        try:
            query = technique.query_template.format(**prepared_values)
        except KeyError as exc:
            missing_name = str(exc).strip("'")
            raise MissingVariableError(
                f"Technique '{technique.id}' is missing required variable '{missing_name}'."
            ) from exc
        except ValueError as exc:
            raise MalformedTemplateError(
                f"Technique '{technique.id}' has a malformed query_template: {exc}"
            ) from exc

        engine_hook = self._engine_hooks.get(technique.engine.strip().lower())
        if engine_hook is not None:
            query = engine_hook(technique, query, prepared_values)

        return QueryRenderResult(
            technique_id=technique.id,
            engine=technique.engine,
            query=query,
            variables=prepared_values,
        )

    def _prepare_values(self, *, technique: Technique, values: Mapping[str, str]) -> dict[str, str]:
        prepared: dict[str, str] = {}
        for variable in technique.variables:
            current_value = values.get(variable.name, "")
            if current_value:
                prepared[variable.name] = current_value
                continue
            if variable.default:
                prepared[variable.name] = variable.default
                continue
            if variable.required:
                raise MissingVariableError(
                    f"Technique '{technique.id}' requires variable '{variable.name}'."
                )
            prepared[variable.name] = ""

        for variable_name in technique.template_variables:
            if variable_name not in prepared:
                raise MissingVariableError(
                    f"Technique '{technique.id}' references undeclared variable '{variable_name}'."
                )

        return prepared

    @staticmethod
    def _normalize_values(values: Mapping[str, object]) -> dict[str, str]:
        return {
            str(key).strip(): str(value).strip()
            for key, value in values.items()
            if str(key).strip()
        }


DEFAULT_QUERY_RENDERER = QueryRenderer()
