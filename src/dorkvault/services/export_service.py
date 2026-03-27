"""File export helpers for rendered queries and technique collections."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Sequence

from dorkvault.core.constants import APP_NAME
from dorkvault.core.exceptions import ExportError
from dorkvault.core.models import Technique


class ExportService:
    """Write rendered queries and technique data to user-selected files."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(APP_NAME)

    def export_rendered_query_text(self, output_path: Path, rendered_query: str) -> Path:
        """Export a rendered query to a plain-text file."""
        cleaned_query = rendered_query.strip()
        if not cleaned_query:
            raise ValueError("Rendered query cannot be empty.")

        try:
            output_path.write_text(f"{cleaned_query}\n", encoding="utf-8")
        except OSError as exc:
            self.logger.exception(
                "Rendered query export failed.",
                extra={
                    "event": "rendered_query_export_failed",
                    "output_path": str(output_path),
                    "error": str(exc),
                },
            )
            raise ExportError("The rendered query could not be exported.") from exc

        self.logger.info(
            "Rendered query exported.",
            extra={
                "event": "rendered_query_exported",
                "output_path": str(output_path),
            },
        )
        return output_path

    def export_techniques_json(
        self,
        output_path: Path,
        techniques: Sequence[Technique],
        *,
        export_name: str = "techniques",
    ) -> Path:
        """Export one or more techniques to a JSON file."""
        serialized_techniques = [self._serialize_technique(technique) for technique in techniques]
        if not serialized_techniques:
            raise ValueError("At least one technique is required to export JSON data.")

        payload = {
            "export_name": export_name,
            "count": len(serialized_techniques),
            "techniques": serialized_techniques,
        }
        try:
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            self.logger.exception(
                "Technique export failed.",
                extra={
                    "event": "technique_export_failed",
                    "output_path": str(output_path),
                    "export_name": export_name,
                    "technique_count": len(serialized_techniques),
                    "error": str(exc),
                },
            )
            raise ExportError("The techniques could not be exported.") from exc

        self.logger.info(
            "Technique export completed.",
            extra={
                "event": "technique_exported",
                "output_path": str(output_path),
                "export_name": export_name,
                "technique_count": len(serialized_techniques),
            },
        )
        return output_path

    def export_favorites_json(self, output_path: Path, techniques: Sequence[Technique]) -> Path:
        """Export a favorites technique collection to JSON."""
        return self.export_techniques_json(
            output_path,
            techniques,
            export_name="favorites",
        )

    @staticmethod
    def _serialize_technique(technique: Technique) -> dict[str, object]:
        return {
            "id": technique.id,
            "name": technique.name,
            "category": technique.category,
            "engine": technique.engine,
            "description": technique.description,
            "query_template": technique.query_template,
            "variables": [
                {
                    "name": variable.name,
                    "description": variable.description,
                    "required": variable.required,
                    "default": variable.default,
                    "example": variable.example,
                }
                for variable in technique.variables
            ],
            "tags": list(technique.tags),
            "example": technique.example,
            "safe_mode": technique.safe_mode,
            "reference": technique.reference,
            "launch_url": technique.launch_url,
            "source_file": technique.source_file,
        }
