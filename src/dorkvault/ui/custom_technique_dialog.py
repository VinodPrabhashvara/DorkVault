"""Dialog for creating validated user-defined techniques."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.exceptions import CustomTechniqueError
from dorkvault.core.models import Technique
from dorkvault.services.custom_technique_service import CustomTechniqueService


class CustomTechniqueDialog(QDialog):
    """Modal dialog for creating a custom technique."""

    def __init__(
        self,
        custom_technique_service: CustomTechniqueService,
        *,
        category_names: list[str],
        engine_names: Iterable[str],
        existing_ids: Iterable[str],
        existing_technique: Technique | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.custom_technique_service = custom_technique_service
        self.existing_ids = list(existing_ids)
        self.existing_technique = existing_technique
        self.saved_technique: Technique | None = None

        self.setWindowTitle("Edit Custom Technique" if existing_technique is not None else "Create Custom Technique")
        self.setModal(True)
        self.resize(560, 560)

        self.summary_label = QLabel(self._summary_text())
        self.summary_label.setWordWrap(True)
        self.error_label = QLabel("")
        self.error_label.setObjectName("emptyStateText")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        self.engine_combo = QComboBox()
        self.description_input = QPlainTextEdit()
        self.query_template_input = QPlainTextEdit()
        self.variables_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.example_input = QLineEdit()
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )

        self._build_ui(category_names, list(engine_names))
        self._connect_signals()
        self._load_existing_values()

    def _build_ui(self, category_names: list[str], engine_names: list[str]) -> None:
        self.name_input.setPlaceholderText("Example: Public S3 Bucket Listing Search")
        self.category_combo.setEditable(True)
        self.engine_combo.setEditable(True)
        self.variables_input.setPlaceholderText("domain, company, keyword")
        self.tags_input.setPlaceholderText("cloud, s3, storage")
        self.example_input.setPlaceholderText("site:s3.amazonaws.com \"example\"")
        self.description_input.setPlaceholderText("Describe what this technique is useful for.")
        self.query_template_input.setPlaceholderText("site:s3.amazonaws.com \"{company}\"")
        self.description_input.setFixedHeight(90)
        self.query_template_input.setFixedHeight(100)

        for category_name in category_names:
            self.category_combo.addItem(category_name, category_name)
        for engine_name in engine_names:
            self.engine_combo.addItem(engine_name, engine_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.error_label)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Category", self.category_combo)
        form_layout.addRow("Engine", self.engine_combo)
        form_layout.addRow("Description", self.description_input)
        form_layout.addRow("Query Template", self.query_template_input)
        form_layout.addRow("Variables", self.variables_input)
        form_layout.addRow("Tags", self.tags_input)
        form_layout.addRow("Example", self.example_input)
        layout.addLayout(form_layout)
        layout.addStretch(1)
        layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.button_box.accepted.connect(self._save)
        self.button_box.rejected.connect(self.reject)

    def _save(self) -> None:
        try:
            if self.existing_technique is None:
                saved_technique = self.custom_technique_service.create_custom_technique(
                    self._build_payload(),
                    existing_ids=self.existing_ids,
                )
            else:
                saved_technique = self.custom_technique_service.update_custom_technique(
                    self.existing_technique.id,
                    self._build_payload(),
                )
        except (CustomTechniqueError, ValueError) as exc:
            self._set_error(str(exc))
            return

        self.saved_technique = saved_technique
        self.error_label.hide()
        self.accept()

    def _load_existing_values(self) -> None:
        if self.existing_technique is None:
            return

        self.name_input.setText(self.existing_technique.name)
        self.category_combo.setCurrentText(self.existing_technique.category)
        self.engine_combo.setCurrentText(self.existing_technique.engine)
        self.description_input.setPlainText(self.existing_technique.description)
        self.query_template_input.setPlainText(self.existing_technique.query_template)
        self.variables_input.setText(", ".join(self.existing_technique.variable_names))
        self.tags_input.setText(", ".join(self.existing_technique.tags))
        self.example_input.setText(self.existing_technique.example)

    def _summary_text(self) -> str:
        if self.existing_technique is not None:
            return "Edit this local custom technique. Built-in technique packs cannot be modified here."
        return "Create a local custom query technique. It will be validated before it is saved."

    def _build_payload(self) -> dict[str, object]:
        return {
            "name": self.name_input.text(),
            "category": self.category_combo.currentText(),
            "engine": self.engine_combo.currentText(),
            "description": self.description_input.toPlainText(),
            "query_template": self.query_template_input.toPlainText(),
            "variables": self.variables_input.text(),
            "tags": self.tags_input.text(),
            "example": self.example_input.text(),
        }

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
