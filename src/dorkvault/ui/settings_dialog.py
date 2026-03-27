"""Dialog for editing local DorkVault application settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.constants import (
    DEFAULT_BROWSER_BEHAVIOR,
    MAX_RECENT_LIMIT,
    MIN_RECENT_LIMIT,
    THEME_DARK,
    THEME_LIGHT,
)
from dorkvault.core.models import AppSettings
from dorkvault.services.settings_service import SettingsService

_BROWSER_BEHAVIOR_LABELS = {
    "same_window": "Current Window",
    "new_window": "New Window",
    "new_tab": "New Tab",
}

_THEME_LABELS = {
    THEME_LIGHT: "Light",
    THEME_DARK: "Dark",
}


class SettingsDialog(QDialog):
    """Modal dialog for editing persistent application settings."""

    def __init__(self, settings_service: SettingsService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings_service = settings_service
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(460, 260)

        self.summary_label = QLabel(
            "Adjust how DorkVault looks and how it handles browser launches and recent history."
        )
        self.summary_label.setWordWrap(True)

        self.theme_combo = QComboBox()
        self.browser_behavior_combo = QComboBox()
        self.recent_limit_spin = QSpinBox()
        self.compact_view_checkbox = QCheckBox("Use compact list view by default")
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )

        self._build_ui()
        self._load_form_values()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self.summary_label)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        self.recent_limit_spin.setRange(MIN_RECENT_LIMIT, MAX_RECENT_LIMIT)

        form_layout.addRow("Theme", self.theme_combo)
        form_layout.addRow("Open in Browser", self.browser_behavior_combo)
        form_layout.addRow("Recent History Limit", self.recent_limit_spin)
        form_layout.addRow("", self.compact_view_checkbox)

        layout.addLayout(form_layout)
        layout.addStretch(1)
        layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _load_form_values(self) -> None:
        settings = self.settings_service.settings

        self.theme_combo.clear()
        for theme_name in self.settings_service.available_themes():
            self.theme_combo.addItem(_THEME_LABELS.get(theme_name, theme_name.title()), theme_name)

        theme_index = self.theme_combo.findData(settings.theme)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)

        self.browser_behavior_combo.clear()
        for behavior, label in _BROWSER_BEHAVIOR_LABELS.items():
            self.browser_behavior_combo.addItem(label, behavior)

        behavior_index = self.browser_behavior_combo.findData(settings.open_in_browser_behavior)
        if behavior_index < 0:
            behavior_index = self.browser_behavior_combo.findData(DEFAULT_BROWSER_BEHAVIOR)
        self.browser_behavior_combo.setCurrentIndex(max(0, behavior_index))

        self.recent_limit_spin.setValue(settings.recent_limit)
        self.compact_view_checkbox.setChecked(settings.compact_view_enabled)

    def selected_settings(self) -> AppSettings:
        """Return settings represented by the current form state."""
        return AppSettings(
            theme=str(self.theme_combo.currentData() or self.settings_service.settings.theme),
            open_in_browser_behavior=str(
                self.browser_behavior_combo.currentData() or DEFAULT_BROWSER_BEHAVIOR
            ),
            recent_limit=int(self.recent_limit_spin.value()),
            compact_view_enabled=self.compact_view_checkbox.isChecked(),
            last_target=self.settings_service.settings.last_target,
        )
