"""Technique details and action panel."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.models import Technique


@dataclass(slots=True, frozen=True)
class TechniqueDetailState:
    """Data needed to render the detail panel for a selected technique."""

    technique: Technique
    tags_text: str
    required_variables_text: str
    preview_query: str
    preview_status: str
    is_favorite: bool
    can_manage_custom: bool


class DetailPanel(QWidget):
    """Right-hand panel that displays the active technique in a compact inspector."""

    copy_requested = Signal()
    launch_requested = Signal()
    favorite_toggled = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stack = QStackedWidget()
        self.content_scroll = QScrollArea()

        self.title_label = QLabel("Technique Details")
        self.category_value = QLabel("-")
        self.engine_value = QLabel("-")
        self.tags_value = QLabel("-")
        self.variables_value = QLabel("-")
        self.description_label = QLabel("")
        self.description_label.setObjectName("detailBodyText")
        self.description_label.setWordWrap(True)
        self.template_preview = QPlainTextEdit()
        self.example_value = QLabel("")
        self.render_status_label = QLabel("")
        self.render_status_label.setObjectName("detailPreviewStatus")
        self.query_preview = QPlainTextEdit()
        self.reference_value = QLabel("")

        self.copy_button = QPushButton("Copy Query")
        self.launch_button = QPushButton("Open Search")
        self.more_button = QToolButton()
        self.more_menu = QMenu(self)
        self.favorite_action = QAction("Add Favorite", self)
        self.edit_action = QAction("Edit Custom Technique", self)
        self.delete_action = QAction("Delete Custom Technique", self)

        self.empty_state = self._build_empty_state()
        self.content_widget = self._build_content_widget()
        self._build_ui()
        self._connect_signals()
        self.clear()

    def _build_ui(self) -> None:
        self.setObjectName("detailPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)
        # Long tags, references, and wrapped descriptions can easily exceed the
        # available panel height as the splitter narrows. Putting the detail
        # content inside a scroll area avoids the clipping/glitching that occurs
        # when Qt has to shrink a non-scrollable stacked page below its natural
        # layout height.
        self.content_scroll.setWidget(self.content_widget)
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setObjectName("detailScrollArea")
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack.addWidget(self.empty_state)
        self.stack.addWidget(self.content_scroll)
        layout.addWidget(self.stack)

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addStretch(1)

        title = QLabel("No Technique Selected")
        title.setObjectName("emptyStateTitle")
        subtitle = QLabel(
            "Pick a technique from the list to understand it quickly, "
            "then copy or open the final query."
        )
        subtitle.setObjectName("emptyStateText")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(2)
        return widget

    def _build_content_widget(self) -> QWidget:
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        widget.setMinimumWidth(0)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 18)
        layout.setSpacing(14)

        self.title_label.setObjectName("detailTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label)

        info_frame = QFrame()
        info_frame.setObjectName("detailInfoFrame")
        info_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        info_layout = QFormLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setHorizontalSpacing(14)
        info_layout.setVerticalSpacing(10)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        info_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        info_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        info_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self._add_info_row(info_layout, "Category", self.category_value)
        self._add_info_row(info_layout, "Engine", self.engine_value)
        self._add_info_row(info_layout, "Tags", self.tags_value)
        self._add_info_row(info_layout, "Input Needed", self.variables_value)
        self._add_info_row(info_layout, "Example", self.example_value)
        self._add_info_row(info_layout, "Reference", self.reference_value)
        layout.addWidget(info_frame)
        layout.addSpacing(2)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addWidget(self.copy_button)
        button_row.addWidget(self.launch_button)
        button_row.addStretch(1)
        button_row.addWidget(self.more_button)
        layout.addLayout(button_row)
        layout.addSpacing(4)

        layout.addWidget(self._section_label("Description"))
        self.description_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self.description_label)

        layout.addWidget(self._section_label("Template"))
        self.template_preview.setReadOnly(True)
        self.template_preview.setPlaceholderText("Technique query template")
        self.template_preview.setObjectName("templatePreview")
        self.template_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.template_preview.setMaximumBlockCount(30)
        self.template_preview.setMinimumHeight(88)
        self.template_preview.setMaximumHeight(124)
        self.template_preview.setTabChangesFocus(True)
        layout.addWidget(self.template_preview)

        layout.addWidget(self._section_label("Rendered Query"))
        self.render_status_label.setWordWrap(True)
        self.render_status_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self.render_status_label)
        self.query_preview.setReadOnly(True)
        self.query_preview.setPlaceholderText(
            "Your final query will appear here once a technique can be rendered."
        )
        self.query_preview.setObjectName("queryPreview")
        self.query_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.query_preview.setMaximumBlockCount(40)
        self.query_preview.setMinimumHeight(184)
        self.query_preview.setTabChangesFocus(True)
        layout.addWidget(self.query_preview)
        layout.addStretch(1)
        return widget

    def _add_info_row(self, layout: QFormLayout, label_text: str, value_widget: QWidget) -> None:
        label = QLabel(label_text)
        label.setObjectName("detailFieldLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        label.setMinimumWidth(92)

        if isinstance(value_widget, QLabel):
            value_widget.setObjectName("detailFieldValue")
            value_widget.setWordWrap(True)
            value_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            value_widget.setMinimumWidth(0)

        layout.addRow(label, value_widget)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("detailSectionLabel")
        return label

    def _connect_signals(self) -> None:
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.launch_button.clicked.connect(self.launch_requested.emit)
        self.favorite_action.triggered.connect(self.favorite_toggled.emit)
        self.edit_action.triggered.connect(self.edit_requested.emit)
        self.delete_action.triggered.connect(self.delete_requested.emit)

        self.more_button.setObjectName("detailOverflowButton")
        self.more_button.setText("Actions")
        self.more_button.setToolTip("Less common actions for this technique")
        self.more_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.copy_button.setMinimumWidth(112)
        self.launch_button.setMinimumWidth(112)
        self.more_button.setMinimumWidth(88)
        self.more_menu.addAction(self.favorite_action)
        self.more_menu.addSeparator()
        self.more_menu.addAction(self.edit_action)
        self.more_menu.addAction(self.delete_action)
        self.more_button.setMenu(self.more_menu)

    def clear(self) -> None:
        self.title_label.setText("Technique Details")
        self.category_value.setText("-")
        self.engine_value.setText("-")
        self.tags_value.setText("-")
        self.variables_value.setText("-")
        self.description_label.setText("")
        self.template_preview.setPlainText("")
        self.example_value.setText("")
        self.reference_value.setText("")
        self.render_status_label.setText("")
        self.query_preview.setPlainText("")
        self.copy_button.setEnabled(False)
        self.launch_button.setEnabled(False)
        self.more_button.setEnabled(False)
        self.set_favorite_state(False)
        self.set_custom_actions_enabled(False)
        self.stack.setCurrentWidget(self.empty_state)

    def set_detail(self, detail_state: TechniqueDetailState) -> None:
        technique = detail_state.technique
        self.title_label.setText(technique.name)
        self.category_value.setText(technique.category)
        self.engine_value.setText(technique.engine)
        self.tags_value.setText(detail_state.tags_text)
        self.variables_value.setText(detail_state.required_variables_text)
        self.description_label.setText(technique.description)
        self.template_preview.setPlainText(technique.query_template)
        self.example_value.setText(technique.example or "None")
        self.reference_value.setText(technique.reference or "None")
        self.render_status_label.setText(detail_state.preview_status)
        self.query_preview.setPlainText(detail_state.preview_query)

        self.copy_button.setEnabled(True)
        self.launch_button.setEnabled(True)
        self.more_button.setEnabled(True)
        self.set_favorite_state(detail_state.is_favorite)
        self.set_custom_actions_enabled(detail_state.can_manage_custom)
        self.stack.setCurrentWidget(self.content_scroll)
        self.content_scroll.verticalScrollBar().setValue(0)

    def set_favorite_state(self, is_favorite: bool) -> None:
        self.favorite_action.setText("Remove Favorite" if is_favorite else "Add Favorite")

    def set_custom_actions_enabled(self, enabled: bool) -> None:
        self.edit_action.setVisible(enabled)
        self.delete_action.setVisible(enabled)
        self.edit_action.setEnabled(enabled)
        self.delete_action.setEnabled(enabled)
