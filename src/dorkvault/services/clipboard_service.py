"""Clipboard-oriented helpers for techniques and rendered queries."""

from __future__ import annotations

from dataclasses import dataclass

from dorkvault.core.models import Technique
from dorkvault.services.technique_preview_service import TechniquePreviewService


@dataclass(slots=True, frozen=True)
class ClipboardCopyResult:
    """Text and feedback to place on the system clipboard."""

    text: str
    feedback_message: str
    source: str


class TechniqueClipboardService:
    """Choose the best text to copy for the current technique state."""

    def __init__(self, preview_service: TechniquePreviewService | None = None) -> None:
        self.preview_service = preview_service or TechniquePreviewService()

    def build_copy_result(self, technique: Technique, target_input: str) -> ClipboardCopyResult:
        preview_state = self.preview_service.build_preview(technique, target_input)
        if not preview_state.render_error:
            return ClipboardCopyResult(
                text=preview_state.preview_query,
                feedback_message="Rendered query copied to clipboard.",
                source="rendered_query",
            )

        return ClipboardCopyResult(
            text=technique.query_template,
            feedback_message="Query template copied to clipboard.",
            source="template",
        )
