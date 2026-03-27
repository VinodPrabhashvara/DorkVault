"""Top toolbar for target input, filters, and compact overflow actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.constants import ALL_TECHNIQUES_LABEL


class TargetToolbar(QWidget):
    """Minimal top bar containing target/search inputs and an overflow menu."""

    target_changed = Signal(str)
    search_changed = Signal(str)
    category_changed = Signal(str)
    open_requested = Signal()
    export_requested = Signal()
    create_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_label = QLabel("DorkVault")
        self.helper_label = QLabel(
            "Tip: enter a target like example.com or Example Corp, then pick a technique to generate a ready-to-use query."
        )
        self.target_input = QLineEdit()
        self.search_input = QLineEdit()
        self.category_combo = QComboBox()
        self.overflow_button = QToolButton()
        self.overflow_menu = QMenu(self)
        self.export_action = QAction("Export...", self)
        self.create_action = QAction("New Custom Technique", self)
        self._build_ui()
        self._connect_signals()
        self.set_action_state(can_export=False)

    def _build_ui(self) -> None:
        self.setObjectName("targetToolbar")
        self.title_label.setObjectName("appTitle")
        self.helper_label.setObjectName("toolbarHelperText")
        self.helper_label.setWordWrap(True)
        self.helper_label.setContentsMargins(0, 2, 0, 0)
        self.target_input.setPlaceholderText("Target: example.com, Example Corp, login, or example-org")
        self.target_input.setToolTip("Target input (Ctrl+L)")
        self.search_input.setPlaceholderText("Search by name, category, engine, tag, or description")
        self.search_input.setToolTip("Search techniques (Ctrl+F)")
        self.category_combo.setObjectName("categoryFilter")
        self.category_combo.addItem("All Categories", ALL_TECHNIQUES_LABEL)
        self.category_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.category_combo.setToolTip("Optional category filter")
        self.category_combo.setMinimumContentsLength(14)

        self.overflow_button.setObjectName("toolbarOverflowButton")
        self.overflow_button.setText("Actions")
        self.overflow_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.overflow_button.setToolTip("Less common actions")
        self.overflow_menu.addAction(self.create_action)
        self.overflow_menu.addSeparator()
        self.overflow_menu.addAction(self.export_action)
        self.overflow_button.setMenu(self.overflow_menu)

        self.target_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.overflow_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.target_input.setMinimumWidth(240)
        self.search_input.setMinimumWidth(220)
        self.category_combo.setMinimumWidth(170)
        self.overflow_button.setMinimumWidth(90)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(12)
        input_row.addWidget(self.target_input, 5)
        input_row.addWidget(self.search_input, 4)
        input_row.addWidget(self.category_combo, 2)
        input_row.addWidget(self.overflow_button)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addLayout(input_row)
        right_layout.addWidget(self.helper_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        layout.addWidget(self.title_label, 0, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(right_layout, 1)

    def _connect_signals(self) -> None:
        self.target_input.textChanged.connect(self.target_changed.emit)
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.target_input.returnPressed.connect(self.open_requested.emit)
        self.category_combo.currentIndexChanged.connect(self._emit_category_change)
        self.export_action.triggered.connect(self.export_requested.emit)
        self.create_action.triggered.connect(self.create_requested.emit)

    def _emit_category_change(self, index: int) -> None:
        category_name = self.category_combo.itemData(index)
        if category_name is None:
            return
        self.category_changed.emit(str(category_name))

    def target_text(self) -> str:
        return self.target_input.text()

    def search_text(self) -> str:
        return self.search_input.text()

    def set_target_text(self, value: str) -> None:
        self.target_input.setText(value)

    def set_search_text(self, value: str) -> None:
        self.search_input.setText(value)

    def focus_target_input(self) -> None:
        self.target_input.setFocus()
        self.target_input.selectAll()

    def focus_search_input(self) -> None:
        self.search_input.setFocus()
        self.search_input.selectAll()

    def set_categories(self, category_names: list[str]) -> None:
        current_category = self.current_category()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", ALL_TECHNIQUES_LABEL)
        for category_name in category_names:
            if category_name == ALL_TECHNIQUES_LABEL:
                continue
            self.category_combo.addItem(category_name, category_name)
        self.set_current_category(current_category)
        self.category_combo.blockSignals(False)

    def set_current_category(self, category_name: str) -> None:
        resolved_category = category_name or ALL_TECHNIQUES_LABEL
        index = self.category_combo.findData(resolved_category)
        if index == -1:
            index = 0
        self.category_combo.blockSignals(True)
        self.category_combo.setCurrentIndex(index)
        self.category_combo.blockSignals(False)

    def current_category(self) -> str:
        return str(self.category_combo.currentData() or ALL_TECHNIQUES_LABEL)

    def set_action_state(self, *, can_export: bool) -> None:
        """Update the compact overflow menu state."""
        self.export_action.setEnabled(can_export)
