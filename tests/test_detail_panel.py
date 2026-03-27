from __future__ import annotations

import pytest

PySide6_QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = PySide6_QtWidgets.QApplication

from dorkvault.core.models import Technique
from dorkvault.widgets.detail_panel import DetailPanel, TechniqueDetailState


def test_detail_panel_reflows_and_scrolls_when_narrow(qapp: QApplication) -> None:
    panel = DetailPanel()
    technique = Technique.from_dict(
        {
            "id": "long-detail-technique",
            "name": "Very Long Technique Name That Should Wrap Correctly In The Right Panel",
            "category": "A Very Long Category Name That Needs Wrapping",
            "engine": "Long Engine Name",
            "description": "Long description " * 30,
            "query_template": "site:{domain} intext:\"very long template content\"",
            "variables": ["domain"],
            "tags": ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"],
            "example": "site:example.com \"deep path\"",
            "safe_mode": True,
            "reference": "https://example.com/reference/with/a/very/long/path/that/should/wrap",
        }
    )
    state = TechniqueDetailState(
        technique=technique,
        tags_text=", ".join(technique.tags),
        required_variables_text="domain",
        preview_query="site:example.com intext:\"preview content\" " * 10,
        preview_status="Ready to copy with a long wrapped status line.",
        is_favorite=False,
        can_manage_custom=False,
    )

    panel.set_detail(state)
    panel.resize(340, 700)
    panel.show()
    qapp.processEvents()

    assert panel.content_scroll.viewport().width() == panel.content_widget.width()
    assert panel.content_scroll.verticalScrollBar().maximum() > 0
    assert panel.reference_value.height() > panel.reference_value.fontMetrics().height()
    assert panel.tags_value.height() > panel.tags_value.fontMetrics().height()
