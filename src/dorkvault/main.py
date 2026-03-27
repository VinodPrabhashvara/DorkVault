"""Executable entrypoint for the DorkVault desktop application."""

from __future__ import annotations

import sys


def main() -> int:
    """Run the application and return a process exit code."""
    try:
        from dorkvault.ui.app import run
    except ModuleNotFoundError as exc:
        missing_name = getattr(exc, "name", "")
        if missing_name == "PySide6":
            print("PySide6 is not installed. Run `pip install -r requirements.txt` first.", file=sys.stderr)
            return 1
        raise

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
