"""Technique list panel for browsing loaded techniques.

The list intentionally uses Qt's model/delegate stack rather than rebuilding child
widgets for each technique. That keeps repaint and selection costs predictable as
the catalog grows into the hundreds of items.
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListView,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.models import Technique

TECHNIQUE_ROLE = Qt.ItemDataRole.UserRole + 1
TECHNIQUE_ID_ROLE = Qt.ItemDataRole.UserRole + 2
TECHNIQUE_FAVORITE_ROLE = Qt.ItemDataRole.UserRole + 3


class TechniqueListViewMode:
    """Available presentation modes for the technique list."""

    LIST = "list"
    CARD = "card"


class TechniqueListModel(QAbstractListModel):
    """Lightweight list model for large technique collections."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._techniques: list[Technique] = []
        self._technique_ids: tuple[str, ...] = ()
        self._technique_rows_by_id: dict[str, int] = {}
        self._favorite_ids: set[str] = set()

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is None:
            parent = QModelIndex()
        if parent.isValid():
            return 0
        return len(self._techniques)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: ANN201
        if not index.isValid() or not (0 <= index.row() < len(self._techniques)):
            return None

        technique = self._techniques[index.row()]
        if role == TECHNIQUE_ROLE:
            return technique
        if role == TECHNIQUE_ID_ROLE:
            return technique.id
        if role == TECHNIQUE_FAVORITE_ROLE:
            return technique.id in self._favorite_ids
        if role == Qt.ItemDataRole.DisplayRole:
            return technique.name
        if role == Qt.ItemDataRole.ToolTipRole:
            return technique.description
        return None

    def set_techniques(self, techniques: list[Technique]) -> bool:
        """Update the visible collection.

        When the visible technique IDs are unchanged we emit a data update instead of
        resetting the whole model. That keeps selection and scroll state stable during
        repeated filter passes, which makes live search feel much smoother.
        """
        new_techniques = list(techniques)
        new_ids = tuple(technique.id for technique in new_techniques)
        structure_changed = new_ids != self._technique_ids

        if structure_changed:
            self.beginResetModel()
            self._techniques = new_techniques
            self._technique_ids = new_ids
            self._rebuild_row_index()
            self.endResetModel()
            return True

        self._techniques = new_techniques
        if self._techniques:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._techniques) - 1, 0)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [
                    Qt.ItemDataRole.DisplayRole,
                    Qt.ItemDataRole.ToolTipRole,
                    TECHNIQUE_ROLE,
                    TECHNIQUE_ID_ROLE,
                    TECHNIQUE_FAVORITE_ROLE,
                ],
            )
        return False

    def set_favorite_ids(self, favorite_ids: list[str] | set[str]) -> None:
        normalized_favorites = {item for item in favorite_ids if item}
        if normalized_favorites == self._favorite_ids:
            return

        self._favorite_ids = normalized_favorites
        if not self._techniques:
            return

        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._techniques) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [TECHNIQUE_FAVORITE_ROLE])

    def index_for_technique_id(self, technique_id: str) -> QModelIndex:
        row = self._technique_rows_by_id.get(technique_id)
        if row is not None:
            return self.index(row, 0)
        return QModelIndex()

    def _rebuild_row_index(self) -> None:
        self._technique_rows_by_id = {
            technique.id: row
            for row, technique in enumerate(self._techniques)
        }


class TechniqueListItemDelegate(QStyledItemDelegate):
    """Paint techniques in a simple list or roomy card layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view_mode = TechniqueListViewMode.LIST
        self._card_margin = 4
        self._content_padding_x = 14
        self._content_padding_top = 11
        self._content_padding_bottom = 10
        self._chip_gap = 6
        self._chip_padding_x = 10
        self._chip_height = 18
        self._title_height = 22
        self._title_to_chip_spacing = 6
        self._chip_to_description_spacing = 7
        self._description_lines = 2

    def set_view_mode(self, view_mode: str) -> None:
        self._view_mode = view_mode

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:  # noqa: ANN001
        technique = index.data(TECHNIQUE_ROLE)
        if technique is None:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = option.rect.adjusted(
            self._card_margin,
            self._card_margin,
            -self._card_margin,
            -self._card_margin,
        )
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        colors = self._resolve_colors(option)

        background = colors["card_background"]
        border = colors["card_border"]
        accent = colors["accent"]
        title_text = colors["title_text"]
        body_text = colors["body_text"]
        chip_background = colors["chip_background"]
        chip_text = colors["chip_text"]
        if is_selected:
            background = colors["card_selected_background"]
            border = colors["card_selected_border"]
            title_text = colors["selected_title_text"]
            body_text = colors["selected_body_text"]
            chip_background = colors["selected_chip_background"]
            chip_text = colors["selected_chip_text"]
        elif is_hovered:
            background = colors["card_hover_background"]

        painter.setPen(QPen(border, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 12, 12)
        if is_selected:
            accent_rect = QRect(rect.left() + 1, rect.top() + 10, 4, rect.height() - 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(accent)
            painter.drawRoundedRect(accent_rect, 2, 2)

        content_rect = rect.adjusted(
            self._content_padding_x,
            self._content_padding_top,
            -self._content_padding_x,
            -self._content_padding_bottom,
        )
        title_font = QFont(option.font)
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        meta_font = QFont(option.font)
        meta_font.setPointSize(max(8, meta_font.pointSize() - 1))
        body_font = QFont(option.font)
        body_metrics = QFontMetrics(body_font)

        description_height = self._description_height(body_metrics)

        title_top = content_rect.top()
        title_rect = QRect(
            content_rect.left(),
            title_top,
            max(80, content_rect.width()),
            self._title_height,
        )
        chip_top = title_top + self._title_height + self._title_to_chip_spacing
        chips_rect = QRect(content_rect.left(), chip_top, content_rect.width(), self._chip_height)
        description_top = chip_top + self._chip_height + self._chip_to_description_spacing
        available_description_height = max(
            0,
            content_rect.bottom() - description_top + 1,
        )
        description_rect = QRect(
            content_rect.left(),
            description_top,
            content_rect.width(),
            min(description_height, available_description_height),
        )

        painter.setFont(title_font)
        painter.setPen(title_text)
        title_metrics = painter.fontMetrics()
        title = title_metrics.elidedText(
            technique.name,
            Qt.TextElideMode.ElideRight,
            title_rect.width(),
        )
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(chip_background)
        painter.setFont(meta_font)
        painter.setPen(chip_text)
        chip_metrics = painter.fontMetrics()
        max_chip_width = max(
            44,
            min(140, (chips_rect.width() - self._chip_gap) // 2),
        )
        category_badge_rect, category_label = self._chip_geometry(
            chip_metrics,
            chips_rect.left(),
            chips_rect.top(),
            technique.category,
            max_chip_width,
        )
        engine_badge_rect, engine_label = self._chip_geometry(
            chip_metrics,
            category_badge_rect.right() + self._chip_gap,
            chips_rect.top(),
            technique.engine,
            max_chip_width,
        )
        painter.drawRoundedRect(category_badge_rect, 9, 9)
        painter.drawRoundedRect(engine_badge_rect, 9, 9)
        painter.drawText(category_badge_rect, Qt.AlignmentFlag.AlignCenter, category_label)
        painter.drawText(engine_badge_rect, Qt.AlignmentFlag.AlignCenter, engine_label)

        painter.setFont(body_font)
        painter.setPen(body_text)
        description = self._elide_text(
            technique.description,
            body_metrics,
            description_rect.width(),
            self._description_lines,
        )
        painter.drawText(
            description_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            description,
        )

        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:  # noqa: ANN001
        _ = index
        body_metrics = QFontMetrics(option.font)
        content_height = (
            self._title_height
            + self._title_to_chip_spacing
            + self._chip_height
            + self._chip_to_description_spacing
            + self._description_height(body_metrics)
        )
        height = (
            self._card_margin * 2
            + self._content_padding_top
            + self._content_padding_bottom
            + content_height
        )
        return QSize(option.rect.width(), height)

    def _chip_geometry(self, metrics, left: int, top: int, text: str, max_width: int):  # noqa: ANN001
        available_text_width = max(18, max_width - (self._chip_padding_x * 2))
        label = self._elide_line(text, metrics, available_text_width)
        chip_width = min(
            max_width,
            max(44, metrics.horizontalAdvance(label) + (self._chip_padding_x * 2)),
        )
        return QRect(left, top, chip_width, self._chip_height), label

    def _description_height(self, metrics) -> int:  # noqa: ANN001
        return metrics.lineSpacing() * self._description_lines

    @staticmethod
    def _elide_text(text: str, metrics, width: int, max_lines: int) -> str:  # noqa: ANN001
        words = text.split()
        if not words:
            return ""

        lines: list[str] = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if metrics.horizontalAdvance(candidate) <= width or not current_line:
                current_line = candidate
                continue

            lines.append(current_line)
            current_line = word
            if len(lines) == max_lines - 1:
                break

        remaining_words = words[len(" ".join(lines + [current_line]).split()):]
        if current_line:
            lines.append(current_line)
        if remaining_words:
            lines[-1] = TechniqueListItemDelegate._elide_line(
                f"{lines[-1]} {' '.join(remaining_words)}",
                metrics,
                width,
            )
        elif lines:
            lines[-1] = TechniqueListItemDelegate._elide_line(lines[-1], metrics, width)

        return "\n".join(lines[:max_lines])

    @staticmethod
    def _elide_line(text: str, metrics, width: int) -> str:  # noqa: ANN001
        if metrics.horizontalAdvance(text) <= width:
            return text

        ellipsis = "..."
        ellipsis_width = metrics.horizontalAdvance(ellipsis)
        if ellipsis_width >= width:
            return ellipsis

        low = 0
        high = len(text)
        while low < high:
            midpoint = (low + high + 1) // 2
            candidate = text[:midpoint].rstrip() + ellipsis
            if metrics.horizontalAdvance(candidate) <= width:
                low = midpoint
            else:
                high = midpoint - 1

        return text[:low].rstrip() + ellipsis

    @staticmethod
    def _resolve_colors(option) -> dict[str, QColor]:  # noqa: ANN001
        application = QApplication.instance()
        active_theme = ""
        if application is not None:
            active_theme = str(application.property("dorkvaultTheme") or "").strip().lower()

        dark_mode = active_theme == "dark"
        if not active_theme:
            dark_mode = option.palette.window().color().lightness() < 128

        if dark_mode:
            return {
                "card_background": QColor("#242a32"),
                "card_border": QColor("#39414c"),
                "card_hover_background": QColor("#2a313b"),
                "card_selected_background": QColor("#2e3948"),
                "card_selected_border": QColor("#6e8fc8"),
                "accent": QColor("#7a9ad4"),
                "title_text": QColor("#f3f6fa"),
                "body_text": QColor("#d6dee6"),
                "meta_text": QColor("#a7b3c0"),
                "chip_background": QColor("#303947"),
                "chip_text": QColor("#d6dee6"),
                "selected_title_text": QColor("#f7fafc"),
                "selected_body_text": QColor("#e3e9f0"),
                "selected_meta_text": QColor("#bcc7d3"),
                "selected_chip_background": QColor("#3a4758"),
                "selected_chip_text": QColor("#e6edf5"),
                "badge_background": QColor("#344259"),
                "badge_text": QColor("#deebff"),
            }

        return {
            "card_background": QColor("#ffffff"),
            "card_border": QColor("#d7dfe8"),
            "card_hover_background": QColor("#f8fafd"),
            "card_selected_background": QColor("#eef3ff"),
            "card_selected_border": QColor("#9cb8e1"),
            "accent": QColor("#5f83c6"),
            "title_text": QColor("#1d2730"),
            "body_text": QColor("#394450"),
            "meta_text": QColor("#607180"),
            "chip_background": QColor("#f1f4f8"),
            "chip_text": QColor("#596978"),
            "selected_title_text": QColor("#1b2530"),
            "selected_body_text": QColor("#36414d"),
            "selected_meta_text": QColor("#5b6e82"),
            "selected_chip_background": QColor("#dfe9fb"),
            "selected_chip_text": QColor("#45607c"),
            "badge_background": QColor("#e8eefb"),
            "badge_text": QColor("#32527f"),
        }


class TechniqueListWidget(QWidget):
    """Reusable technique browser panel with large-catalog-friendly rendering."""

    technique_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_label = QLabel("Techniques")
        self.count_label = QLabel("Showing 0 techniques")
        self.summary_label = QLabel("Choose a technique to preview the final query on the right.")
        self.stack = QStackedWidget()
        self.empty_state = self._build_empty_state()
        self.list_view = QListView()
        self.model = TechniqueListModel(self)
        self.delegate = TechniqueListItemDelegate(self.list_view)
        self._build_ui()
        self._connect_signals()
        self.set_view_mode(TechniqueListViewMode.LIST)

    def _build_ui(self) -> None:
        self.setObjectName("techniqueList")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_label.setObjectName("panelTitle")
        self.count_label.setObjectName("resultCount")
        self.summary_label.setObjectName("panelSummary")
        self.summary_label.setWordWrap(True)

        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setObjectName("techniqueListView")
        self.list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.list_view.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setLayoutMode(QListView.LayoutMode.Batched)
        self.list_view.setBatchSize(64)
        self.list_view.setAlternatingRowColors(False)
        self.list_view.setMouseTracking(True)
        self.list_view.setSpacing(10)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.count_label)
        header_layout.addWidget(self.summary_label)

        self.stack.addWidget(self.empty_state)
        self.stack.addWidget(self.list_view)

        layout.addLayout(header_layout)
        layout.addWidget(self.stack, 1)

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addStretch(1)

        title = QLabel("No Matching Techniques")
        title.setObjectName("emptyStateTitle")
        message = QLabel(
            "No techniques match the current target, search text, and category filters. "
            "Try clearing one of them."
        )
        message.setObjectName("emptyStateText")
        message.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch(2)
        return widget

    def _connect_signals(self) -> None:
        self.list_view.selectionModel().currentChanged.connect(self._emit_selection)

    def set_view_mode(self, view_mode: str) -> None:
        self.delegate.set_view_mode(view_mode)
        self.list_view.doItemsLayout()
        self.list_view.viewport().update()

    def set_compact_view_enabled(self, enabled: bool) -> None:
        """Apply the persisted compact-view preference."""
        self.set_view_mode(TechniqueListViewMode.LIST if enabled else TechniqueListViewMode.CARD)

    def set_techniques(self, techniques: list[Technique]) -> None:
        self.model.set_techniques(techniques)
        result_count = len(techniques)
        label = "technique" if result_count == 1 else "techniques"
        self.count_label.setText(f"Showing {result_count} {label}")
        self.stack.setCurrentWidget(self.list_view if techniques else self.empty_state)
        if not techniques:
            self.clear_selection()

    def set_result_summary(
        self,
        *,
        visible_count: int,
        source_count: int,
        search_text: str = "",
        category_name: str = "",
    ) -> None:
        """Explain the current result set in plain language.

        Keeping this text in the widget lets the main window pass only filter state
        while the presentation wording stays centralized with the list panel.
        """
        if source_count <= 0:
            self.count_label.setText("No techniques available")
        elif (
            visible_count == source_count
            and not search_text.strip()
            and not category_name.strip()
        ):
            label = "technique" if visible_count == 1 else "techniques"
            self.count_label.setText(f"Showing all {visible_count} {label}")
        else:
            label = "technique" if visible_count == 1 else "techniques"
            self.count_label.setText(f"Showing {visible_count} of {source_count} {label}")

        summary_parts: list[str] = []
        if category_name.strip():
            summary_parts.append(f"category: {category_name}")
        if search_text.strip():
            summary_parts.append(f"search: {search_text.strip()}")

        if summary_parts:
            self.summary_label.setText(
                "Filtered by "
                + " | ".join(summary_parts)
                + ". Select a technique to preview the final query."
            )
            return

        self.summary_label.setText("Choose a technique to preview the final query on the right.")

    def set_favorite_ids(self, favorite_ids: list[str] | set[str]) -> None:
        self.model.set_favorite_ids(favorite_ids)

    def has_technique(self, technique_id: str) -> bool:
        return self.model.index_for_technique_id(technique_id).isValid()

    def clear_selection(self) -> None:
        self.list_view.clearSelection()
        self.list_view.setCurrentIndex(QModelIndex())

    def _emit_selection(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        technique_id = current.data(TECHNIQUE_ID_ROLE)
        if technique_id:
            self.technique_selected.emit(str(technique_id))

    def select_first(self) -> None:
        if self.model.rowCount() > 0:
            self.list_view.setCurrentIndex(self.model.index(0, 0))

    def select_technique(self, technique_id: str) -> bool:
        index = self.model.index_for_technique_id(technique_id)
        if index.isValid():
            self.list_view.setCurrentIndex(index)
            self.list_view.scrollTo(index, QListView.ScrollHint.PositionAtCenter)
            return True
        return False
