"""Build user-facing preview state for selected techniques."""

from __future__ import annotations

from dataclasses import dataclass

from dorkvault.core.exceptions import QueryRenderError
from dorkvault.core.models import Technique
from dorkvault.services.target_normalization import normalize_target_input


@dataclass(slots=True, frozen=True)
class TechniquePreviewState:
    """Preview output for the detail panel."""

    preview_query: str
    status_text: str
    render_error: str = ""


class TechniquePreviewService:
    """Create friendly preview text for the current technique and target input."""

    def build_preview(self, technique: Technique, target_input: str) -> TechniquePreviewState:
        fallback_preview = technique.example or technique.query_template
        cleaned_target = target_input.strip()

        if not cleaned_target:
            if technique.primary_variable_name is None and technique.required_variables:
                required_names = ", ".join(variable.name for variable in technique.required_variables)
                return TechniquePreviewState(
                    preview_query=fallback_preview,
                    status_text=f"This technique needs more than one input: {required_names}. Showing the saved example for now.",
                )

            if technique.primary_variable_name:
                return TechniquePreviewState(
                    preview_query=fallback_preview,
                    status_text=f"Enter {technique.primary_variable_name} above to render the final query.",
                )

            return TechniquePreviewState(
                preview_query=fallback_preview,
                status_text="This technique does not need a target input. Showing the stored example query.",
            )

        if technique.primary_variable_name is None:
            required_names = ", ".join(variable.name for variable in technique.required_variables)
            return TechniquePreviewState(
                preview_query=fallback_preview,
                status_text=f"Cannot render from one target input. This technique needs: {required_names}.",
                render_error="multiple_variables_required",
            )

        normalization_result = normalize_target_input(
            cleaned_target,
            variable_name=technique.primary_variable_name,
        )
        try:
            rendered_query = technique.build_query(cleaned_target)
        except (QueryRenderError, ValueError) as exc:
            return TechniquePreviewState(
                preview_query=fallback_preview,
                status_text=f"The final preview could not be rendered yet: {exc}",
                render_error=str(exc),
            )

        status_text = (
            f"Ready to use. Rendered using {technique.primary_variable_name}: "
            f"{normalization_result.normalized_value}"
        )
        if normalization_result.helper_text:
            status_text += f"\n{normalization_result.helper_text}"

        return TechniquePreviewState(
            preview_query=rendered_query,
            status_text=status_text,
        )
