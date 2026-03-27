"""Reusable left sidebar for DorkVault navigation and category filtering."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.constants import ALL_TECHNIQUES_LABEL
from dorkvault.core.models import TechniqueCategoryGroup
from dorkvault.services.technique_loader import DEFAULT_CATEGORY_GROUP_ID

SECTION_ALL = "all_techniques"
SECTION_FAVORITES = "favorites"
SECTION_RECENT = "recent"
SECTION_CATEGORIES = "categories"
SECTION_SETTINGS = "settings"
SECTION_ABOUT = "about"

ITEM_KIND_ROLE = Qt.ItemDataRole.UserRole
ITEM_VALUE_ROLE = Qt.ItemDataRole.UserRole + 1
ITEM_KIND_GROUP = "group"
ITEM_KIND_CATEGORY = "category"


@dataclass(slots=True, frozen=True)
class SidebarNavItem:
    """Simple sidebar navigation descriptor."""

    section_id: str
    label: str


class SidebarWidget(QWidget):
    """Left-hand navigation and grouped category filter panel."""

    section_changed = Signal(str)
    category_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_label = QLabel("Browse")
        self.summary_label = QLabel("Choose a section or category.")
        self.library_title = QLabel("Library")
        self.primary_nav_group = QButtonGroup(self)
        self.primary_nav_group.setExclusive(True)
        self.primary_buttons: dict[str, QPushButton] = {}
        self.utility_buttons: dict[str, QPushButton] = {}
        self.categories_title = QLabel("Categories")
        self.utility_title = QLabel("Application")
        self.category_tree = QTreeWidget()
        self._category_items: dict[str, QTreeWidgetItem] = {}
        self._current_section = SECTION_ALL
        self._current_category = ALL_TECHNIQUES_LABEL
        self._suspend_signals = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(11)

        self.title_label.setObjectName("panelTitle")
        self.summary_label.setObjectName("panelSummary")
        self.summary_label.setWordWrap(True)
        self.library_title.setObjectName("sidebarSectionLabel")
        self.categories_title.setObjectName("sidebarSectionLabel")
        self.utility_title.setObjectName("sidebarSectionLabel")
        self.category_tree.setObjectName("sidebarCategoryTree")

        self.category_tree.setHeaderHidden(True)
        self.category_tree.setRootIsDecorated(False)
        self.category_tree.setIndentation(12)
        self.category_tree.setUniformRowHeights(True)
        self.category_tree.setExpandsOnDoubleClick(False)
        self.category_tree.setAnimated(False)
        self.category_tree.setItemsExpandable(True)
        self.category_tree.setAllColumnsShowFocus(True)
        self.category_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addSpacing(2)
        layout.addWidget(self.library_title)

        for item in (
            SidebarNavItem(SECTION_ALL, "All Techniques"),
            SidebarNavItem(SECTION_FAVORITES, "Favorites"),
            SidebarNavItem(SECTION_RECENT, "Recent"),
        ):
            button = self._create_nav_button(item.label, item.section_id)
            self.primary_nav_group.addButton(button)
            self.primary_buttons[item.section_id] = button
            layout.addWidget(button)

        layout.addSpacing(6)
        layout.addWidget(self.categories_title)
        layout.addWidget(self.category_tree, 1)

        layout.addSpacing(6)
        layout.addWidget(self.utility_title)
        for item in (
            SidebarNavItem(SECTION_SETTINGS, "Settings"),
            SidebarNavItem(SECTION_ABOUT, "About"),
        ):
            button = self._create_utility_button(item.label, item.section_id)
            self.utility_buttons[item.section_id] = button
            layout.addWidget(button)

        self.primary_buttons[SECTION_ALL].setChecked(True)
        self.category_tree.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _connect_signals(self) -> None:
        self.primary_nav_group.buttonClicked.connect(self._handle_primary_nav_clicked)
        self.category_tree.currentItemChanged.connect(self._handle_category_selected)
        self.category_tree.itemClicked.connect(self._handle_item_clicked)

    def _create_nav_button(self, label: str, section_id: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("sidebarNavButton")
        button.setCheckable(True)
        button.setProperty("sectionId", section_id)
        return button

    def _create_utility_button(self, label: str, section_id: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("sidebarUtilityButton")
        button.clicked.connect(lambda _checked=False, value=section_id: self._activate_section(value))
        return button

    def set_category_groups(
        self,
        category_groups: list[TechniqueCategoryGroup],
        counts_by_category: dict[str, int],
    ) -> None:
        previous_category = self._current_category
        total_categories = sum(len(group.categories) for group in category_groups)
        total_groups = len([group for group in category_groups if group.categories])
        total_techniques = counts_by_category.get(ALL_TECHNIQUES_LABEL, 0)

        self._suspend_signals = True
        tree_signal_blocker = QSignalBlocker(self.category_tree)
        try:
            self.category_tree.clear()
            self._category_items.clear()

            visible_groups = [group for group in category_groups if group.categories]
            flatten_default_group = (
                len(visible_groups) == 1
                and visible_groups[0].id == DEFAULT_CATEGORY_GROUP_ID
            )

            for group in visible_groups:
                if flatten_default_group:
                    for category in group.categories:
                        self._add_category_item(
                            parent=None,
                            category_name=category.name,
                            count=counts_by_category.get(category.name, len(category.techniques)),
                        )
                    continue

                group_count = sum(
                    counts_by_category.get(category.name, len(category.techniques))
                    for category in group.categories
                )
                group_item = QTreeWidgetItem([f"{group.name} ({group_count})"])
                group_item.setData(0, ITEM_KIND_ROLE, ITEM_KIND_GROUP)
                group_item.setData(0, ITEM_VALUE_ROLE, group.id)
                group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                group_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
                self.category_tree.addTopLevelItem(group_item)

                for category in group.categories:
                    self._add_category_item(
                        parent=group_item,
                        category_name=category.name,
                        count=counts_by_category.get(category.name, len(category.techniques)),
                    )
                group_item.setExpanded(True)

            if total_groups > 1:
                self.summary_label.setText(
                    f"{total_techniques} techniques across {total_categories} categories in {total_groups} groups"
                )
            else:
                self.summary_label.setText(f"{total_techniques} techniques in {total_categories} categories")

            self._restore_selected_category(previous_category)
        finally:
            del tree_signal_blocker
            self._suspend_signals = False

    def _add_category_item(
        self,
        *,
        parent: QTreeWidgetItem | None,
        category_name: str,
        count: int,
    ) -> None:
        item = QTreeWidgetItem([f"{category_name} ({count})"])
        item.setData(0, ITEM_KIND_ROLE, ITEM_KIND_CATEGORY)
        item.setData(0, ITEM_VALUE_ROLE, category_name)
        if parent is None:
            self.category_tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self._category_items[category_name] = item

    def _restore_selected_category(self, previous_category: str) -> None:
        target_category = previous_category if previous_category in self._category_items else ""
        if not target_category and self._category_items:
            target_category = next(iter(self._category_items))

        if not target_category:
            self._current_category = ALL_TECHNIQUES_LABEL
            self.category_tree.setCurrentItem(None)
            return

        self._current_category = target_category
        self.category_tree.setCurrentItem(self._category_items[target_category])

    def _handle_primary_nav_clicked(self, button: QPushButton) -> None:
        section_id = str(button.property("sectionId") or SECTION_ALL)
        self._activate_section(section_id)

    def _handle_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        if item.data(0, ITEM_KIND_ROLE) == ITEM_KIND_GROUP:
            item.setExpanded(not item.isExpanded())

    def _handle_category_selected(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None or current.data(0, ITEM_KIND_ROLE) != ITEM_KIND_CATEGORY:
            return

        self._current_category = str(current.data(0, ITEM_VALUE_ROLE) or ALL_TECHNIQUES_LABEL)
        self._set_primary_checked(False)
        self._activate_section(SECTION_CATEGORIES, emit_category=True)

    def _activate_section(self, section_id: str, *, emit_category: bool = False) -> None:
        self._current_section = section_id
        if section_id in self.primary_buttons:
            self.primary_buttons[section_id].setChecked(True)
        elif section_id != SECTION_CATEGORIES:
            self._set_primary_checked(False)

        if self._suspend_signals:
            return

        self.section_changed.emit(section_id)
        if emit_category:
            self.category_selected.emit(self._current_category)

    def _set_primary_checked(self, checked: bool) -> None:
        previous_exclusive = self.primary_nav_group.exclusive()
        self.primary_nav_group.setExclusive(False)
        for button in self.primary_buttons.values():
            button.setChecked(checked and button is self.primary_buttons.get(self._current_section))
            if not checked:
                button.setChecked(False)
        self.primary_nav_group.setExclusive(previous_exclusive)

    def current_section(self) -> str:
        return self._current_section

    def current_category(self) -> str:
        if self._current_section == SECTION_CATEGORIES:
            return self._current_category
        return ALL_TECHNIQUES_LABEL

    def set_section(self, section_id: str) -> None:
        """Programmatically activate a sidebar section."""
        self._activate_section(section_id)

    def select_all(self) -> None:
        """Programmatically select the all-techniques section."""
        self.set_section(SECTION_ALL)

    def select_category(self, category_name: str) -> None:
        """Programmatically switch to category mode and select a category item."""
        category_item = self._category_items.get(category_name)
        if category_item is None:
            self.select_all()
            return

        parent_item = category_item.parent()
        if parent_item is not None:
            parent_item.setExpanded(True)

        self._suspend_signals = True
        tree_signal_blocker = QSignalBlocker(self.category_tree)
        try:
            self.category_tree.setCurrentItem(category_item)
            self._current_category = category_name
        finally:
            del tree_signal_blocker
            self._suspend_signals = False
        self._set_primary_checked(False)
        self._activate_section(SECTION_CATEGORIES, emit_category=True)
