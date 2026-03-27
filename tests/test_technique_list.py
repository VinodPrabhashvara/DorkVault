from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QListView, QStyleOptionViewItem

from dorkvault.widgets.technique_list import TechniqueListWidget


def test_technique_list_uses_cleaner_spacing_and_compact_cards(qapp, make_technique) -> None:
    widget = TechniqueListWidget()
    widget.set_techniques(
        [
            make_technique(
                description=(
                    "Search indexed content for exposed admin portals and document trails. " * 3
                ),
                tags=["google", "admin", "login", "docs", "sensitive"],
            ),
            make_technique(
                id="second-technique",
                name="Longer Named Workflow Discovery Technique For Validation",
                category="Code Search",
                engine="GitHub",
                description=(
                    "Search public repositories for workflow files, internal naming patterns, "
                    "and secrets references. " * 3
                ),
                tags=["github", "workflow", "code", "scan"],
            ),
        ]
    )

    widget.resize(760, 520)
    widget.show()
    qapp.processEvents()

    assert widget.list_view.spacing() == 10
    assert widget.list_view.verticalScrollMode() == QListView.ScrollMode.ScrollPerPixel

    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 620, 0)
    option.font = widget.font()
    metrics = widget.fontMetrics()
    index = widget.model.index(0, 0)

    widget.set_compact_view_enabled(True)
    compact_hint = widget.delegate.sizeHint(option, index)
    compact_description = widget.delegate._elide_text(  # noqa: SLF001
        str(index.data(Qt.ItemDataRole.ToolTipRole) or ""),
        metrics,
        420,
        2,
    )

    widget.set_compact_view_enabled(False)
    card_hint = widget.delegate.sizeHint(option, index)
    card_description = widget.delegate._elide_text(  # noqa: SLF001
        str(index.data(Qt.ItemDataRole.ToolTipRole) or ""),
        metrics,
        420,
        2,
    )

    expected_height = (
        (widget.delegate._card_margin * 2)  # noqa: SLF001
        + widget.delegate._content_padding_top  # noqa: SLF001
        + widget.delegate._content_padding_bottom  # noqa: SLF001
        + widget.delegate._title_height  # noqa: SLF001
        + widget.delegate._title_to_chip_spacing  # noqa: SLF001
        + widget.delegate._chip_height  # noqa: SLF001
        + widget.delegate._chip_to_description_spacing  # noqa: SLF001
        + widget.delegate._description_height(metrics)  # noqa: SLF001
    )
    assert compact_hint.height() == expected_height
    assert card_hint.height() == expected_height
    assert compact_description.count("\n") <= 1
    assert card_description.count("\n") <= 1
    assert card_description.endswith("...")
