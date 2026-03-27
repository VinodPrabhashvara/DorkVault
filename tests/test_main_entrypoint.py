from __future__ import annotations

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import dorkvault.main


def test_main_script_executes_application_entrypoint(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "dorkvault.ui.app",
        SimpleNamespace(run=lambda: 42),
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(dorkvault.main.__file__)), run_name="__main__")

    assert exc_info.value.code == 42
