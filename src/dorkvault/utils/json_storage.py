"""Small helpers for consistent JSON persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> None:
    """Write JSON to disk with a temporary file and atomic replace.

    The caller owns error handling and logging so this helper stays reusable
    across services with different exception and message requirements.
    """
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=indent, sort_keys=sort_keys)
        os.replace(temporary_path, path)
    except OSError:
        _safe_unlink(temporary_path)
        raise


def _safe_unlink(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError:
        return
