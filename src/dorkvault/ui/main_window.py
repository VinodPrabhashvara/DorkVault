"""Main application window."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from dorkvault.core.config import DEFAULT_APP_CONFIG
from dorkvault.core.constants import ALL_TECHNIQUES_LABEL, APP_NAME, APP_VERSION
from dorkvault.core.exceptions import (
    BrowserIntegrationError,
    CustomTechniqueError,
    DataValidationError,
    ExportError,
    FavoritesError,
    QueryRenderError,
    RecentHistoryError,
    SettingsError,
    TechniqueLoadError,
)
from dorkvault.core.models import AppSettings, Technique
from dorkvault.services.clipboard_service import TechniqueClipboardService
from dorkvault.services.custom_technique_service import CustomTechniqueService
from dorkvault.services.export_service import ExportService
from dorkvault.services.favorites_service import FavoritesService
from dorkvault.services.launcher_service import LauncherService
from dorkvault.services.recent_history_service import RecentHistoryService
from dorkvault.services.settings_service import SettingsService
from dorkvault.services.technique_filter_service import (
    TechniqueFilterCriteria,
    TechniqueFilterService,
)
from dorkvault.services.technique_preview_service import TechniquePreviewService
from dorkvault.services.technique_repository import TechniqueRepository
from dorkvault.services.theme_manager import ThemeManager
from dorkvault.ui.custom_technique_dialog import CustomTechniqueDialog
from dorkvault.ui.settings_dialog import SettingsDialog
from dorkvault.utils.resource_loader import load_icon
from dorkvault.widgets.detail_panel import DetailPanel, TechniqueDetailState
from dorkvault.widgets.sidebar import (
    SECTION_ABOUT,
    SECTION_ALL,
    SECTION_CATEGORIES,
    SECTION_FAVORITES,
    SECTION_RECENT,
    SECTION_SETTINGS,
    SidebarWidget,
)
from dorkvault.widgets.target_toolbar import TargetToolbar
from dorkvault.widgets.technique_list import TechniqueListWidget


class MainWindow(QMainWindow):
    """Primary desktop window for browsing and launching techniques."""

    _STANDARD_WINDOW_FLAGS = (
        Qt.WindowType.Window
        | Qt.WindowType.WindowTitleHint
        | Qt.WindowType.WindowSystemMenuHint
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
    )

    def __init__(
        self,
        settings_service: SettingsService | None = None,
        favorites_service: FavoritesService | None = None,
        recent_history_service: RecentHistoryService | None = None,
    ) -> None:
        super().__init__()
        self.logger = logging.getLogger(APP_NAME)
        self.settings_service = settings_service or SettingsService()
        self.theme_manager = ThemeManager()
        self.favorites_service = favorites_service or FavoritesService(
            legacy_settings_path=self.settings_service.settings_path
        )
        self.recent_history_service = recent_history_service or RecentHistoryService(
            legacy_settings_path=self.settings_service.settings_path
        )
        self.repository = TechniqueRepository()
        self.custom_technique_service = CustomTechniqueService()
        self.export_service = ExportService()
        self.filter_service = TechniqueFilterService()
        self.launcher = LauncherService()
        self.preview_service = TechniquePreviewService()
        self.clipboard_service = TechniqueClipboardService(self.preview_service)
        self.current_technique: Technique | None = None
        self._visible_techniques: list[Technique] = []
        self._last_browsing_section = SECTION_ALL
        self._last_browsing_category = ALL_TECHNIQUES_LABEL
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(140)
        self._shortcuts: list[QShortcut] = []
        self.workspace_splitter: QSplitter | None = None

        self._configure_native_window_frame()
        self.setWindowTitle(APP_NAME)

        self.target_toolbar = TargetToolbar()
        self.sidebar = SidebarWidget()
        self.technique_list = TechniqueListWidget()
        self.detail_panel = DetailPanel()

        self._build_ui()
        self._apply_startup_geometry()
        self._connect_signals()
        self._setup_shortcuts()
        self._setup_focus_order()
        self._load_data()

    def _configure_native_window_frame(self) -> None:
        """Force a standard decorated desktop window with native caption buttons."""
        self.setWindowFlags(self._STANDARD_WINDOW_FLAGS)

        application = QApplication.instance()
        if application is not None and not application.windowIcon().isNull():
            self.setWindowIcon(application.windowIcon())
            return

        fallback_icon = load_icon("app_icon.ico", fallback_name="app_icon.svg")
        if not fallback_icon.isNull():
            self.setWindowIcon(fallback_icon)

    def _apply_startup_geometry(self) -> None:
        """Restore a valid saved geometry or use a safe centered fallback."""
        startup_screen = self._startup_screen()
        available_geometry = startup_screen.availableGeometry()
        startup_geometry = self._validated_saved_geometry()
        if startup_geometry is None:
            startup_geometry = self._safe_default_geometry(available_geometry)
        else:
            saved_screen_geometry = self._screen_geometry_for_rect(startup_geometry)
            if saved_screen_geometry is not None:
                available_geometry = saved_screen_geometry

        self.setMinimumSize(self._effective_minimum_size(available_geometry))
        self.resize(startup_geometry.size())
        self.move(startup_geometry.topLeft())

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(16, 16, 16, 16)
        central_layout.setSpacing(14)
        central_layout.addWidget(self.target_toolbar)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setObjectName("workspaceSplitter")
        self.workspace_splitter.setHandleWidth(10)
        self.workspace_splitter.addWidget(self.sidebar)
        self.workspace_splitter.addWidget(self.technique_list)
        self.workspace_splitter.addWidget(self.detail_panel)
        self.workspace_splitter.setSizes(
            [
                DEFAULT_APP_CONFIG.sidebar_default_width,
                DEFAULT_APP_CONFIG.list_default_width,
                DEFAULT_APP_CONFIG.detail_default_width,
            ]
        )
        self.workspace_splitter.setStretchFactor(0, 0)
        self.workspace_splitter.setStretchFactor(1, 5)
        self.workspace_splitter.setStretchFactor(2, 4)
        self.workspace_splitter.setChildrenCollapsible(False)
        central_layout.addWidget(self.workspace_splitter, 1)

        self.setCentralWidget(central_widget)

        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

        self.sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.technique_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.detail_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.sidebar.setMinimumWidth(210)
        self.sidebar.setMaximumWidth(300)
        self.technique_list.setMinimumWidth(390)
        self.detail_panel.setMinimumWidth(380)

    def _startup_screen(self):
        """Choose the safest screen for first-show placement."""
        cursor_screen = QGuiApplication.screenAt(QCursor.pos())
        if cursor_screen is not None:
            return cursor_screen

        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is not None:
            return primary_screen

        screens = QGuiApplication.screens()
        if screens:
            return screens[0]
        raise RuntimeError("No screens are available for window placement.")

    def _available_screen_geometries(self) -> list[QRect]:
        return [screen.availableGeometry() for screen in QGuiApplication.screens()]

    def _validated_saved_geometry(self) -> QRect | None:
        saved_geometry = self.settings_service.settings.window_geometry
        if not saved_geometry:
            return None

        candidate = QRect(
            saved_geometry["x"],
            saved_geometry["y"],
            saved_geometry["width"],
            saved_geometry["height"],
        )
        for available_geometry in self._available_screen_geometries():
            if (
                self._geometry_fits_screen(candidate, available_geometry)
                and candidate.width() >= self._safe_minimum_width(available_geometry)
                and candidate.height() >= self._safe_minimum_height(available_geometry)
            ):
                return candidate
        return None

    def _screen_geometry_for_rect(self, geometry: QRect) -> QRect | None:
        for available_geometry in self._available_screen_geometries():
            if self._geometry_fits_screen(geometry, available_geometry):
                return available_geometry
        return None

    def _safe_default_geometry(self, available_geometry: QRect) -> QRect:
        width = min(
            available_geometry.width(),
            max(
                self._safe_minimum_width(available_geometry),
                int(available_geometry.width() * 0.88),
            ),
        )
        height = min(
            available_geometry.height(),
            max(
                self._safe_minimum_height(available_geometry),
                int(available_geometry.height() * 0.88),
            ),
        )
        width = max(1, width)
        height = max(1, height)

        startup_rect = QRect(0, 0, width, height)
        startup_rect.moveCenter(available_geometry.center())
        startup_rect.moveLeft(max(available_geometry.left(), startup_rect.left()))
        startup_rect.moveTop(max(available_geometry.top(), startup_rect.top()))
        if startup_rect.right() > available_geometry.right():
            startup_rect.moveRight(available_geometry.right())
        if startup_rect.bottom() > available_geometry.bottom():
            startup_rect.moveBottom(available_geometry.bottom())
        return startup_rect

    def _geometry_fits_screen(self, geometry: QRect, available_geometry: QRect) -> bool:
        return (
            geometry.width() > 0
            and geometry.height() > 0
            and geometry.width() <= available_geometry.width()
            and geometry.height() <= available_geometry.height()
            and geometry.left() >= available_geometry.left()
            and geometry.top() >= available_geometry.top()
            and geometry.right() <= available_geometry.right()
            and geometry.bottom() <= available_geometry.bottom()
        )

    def _effective_minimum_size(self, available_geometry: QRect) -> QSize:
        return QSize(
            self._safe_minimum_width(available_geometry),
            self._safe_minimum_height(available_geometry),
        )

    def _safe_minimum_width(self, available_geometry: QRect) -> int:
        return min(DEFAULT_APP_CONFIG.minimum_width, available_geometry.width())

    def _safe_minimum_height(self, available_geometry: QRect) -> int:
        return min(DEFAULT_APP_CONFIG.minimum_height, available_geometry.height())

    def _current_window_geometry(self) -> QRect:
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        return QRect(geometry)

    def _serialized_window_geometry(self) -> dict[str, int]:
        geometry = self._current_window_geometry()
        return {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }

    def _connect_signals(self) -> None:
        # Search is debounced so we do not rebuild filter results on every keypress
        # while the user is still typing.
        self.target_toolbar.search_changed.connect(self._schedule_filter_update)
        self.target_toolbar.target_changed.connect(self._refresh_detail_panel)
        self.target_toolbar.category_changed.connect(self._handle_toolbar_category_change)
        self.target_toolbar.open_requested.connect(self._launch_current_technique)
        self.target_toolbar.export_requested.connect(self._open_export_dialog)
        self.target_toolbar.create_requested.connect(self._create_custom_technique)
        self.sidebar.section_changed.connect(self._handle_sidebar_section_change)
        self.sidebar.category_selected.connect(self._apply_filters)
        self.technique_list.technique_selected.connect(self._handle_technique_selected)
        self.detail_panel.copy_requested.connect(self._copy_current_query)
        self.detail_panel.launch_requested.connect(self._launch_current_technique)
        self.detail_panel.favorite_toggled.connect(self._toggle_favorite)
        self.detail_panel.edit_requested.connect(self._edit_current_custom_technique)
        self.detail_panel.delete_requested.connect(self._delete_current_custom_technique)
        self._filter_timer.timeout.connect(self._apply_filters)

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts in one place so behaviors stay easy to audit."""
        self._register_shortcut("Ctrl+F", self._focus_search)
        self._register_shortcut("Ctrl+L", self._focus_target)
        self._register_shortcut("Ctrl+C", self._handle_copy_shortcut)
        self._register_shortcut("Ctrl+O", self._handle_open_shortcut)
        self._register_shortcut("Ctrl+E", self._handle_export_shortcut)

    def _setup_focus_order(self) -> None:
        """Keep keyboard navigation aligned with the normal task flow."""
        self.setTabOrder(self.target_toolbar.target_input, self.target_toolbar.search_input)
        self.setTabOrder(self.target_toolbar.search_input, self.target_toolbar.category_combo)
        self.setTabOrder(self.target_toolbar.category_combo, self.technique_list.list_view)
        self.setTabOrder(self.technique_list.list_view, self.detail_panel.copy_button)
        self.setTabOrder(self.detail_panel.copy_button, self.detail_panel.launch_button)
        self.setTabOrder(self.detail_panel.launch_button, self.detail_panel.more_button)

    def _register_shortcut(self, key_sequence: str, callback) -> None:  # noqa: ANN001
        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)

    def _load_data(self) -> None:
        self._reload_repository()
        QTimer.singleShot(0, self.target_toolbar.focus_target_input)

    def _reload_repository(self, *, selected_technique_id: str | None = None) -> None:
        try:
            self.repository.load()
            self.sidebar.set_category_groups(
                self.repository.category_groups(),
                self.repository.counts_by_category(),
            )
            self.target_toolbar.set_categories(self.repository.category_names())
            if not self.target_toolbar.target_text():
                self.target_toolbar.set_target_text(self.settings_service.settings.last_target)
            self._apply_settings_to_runtime(self.settings_service.settings)
            self.technique_list.set_favorite_ids(self.favorites_service.all_ids())
            self._apply_filters(ALL_TECHNIQUES_LABEL)
            if selected_technique_id:
                self._focus_technique(selected_technique_id)
            self.statusBar().showMessage(
                f"Loaded {len(self.repository.all_techniques())} techniques.",
                5000,
            )
            self._sync_toolbar_state()
        except (
            TechniqueLoadError,
            DataValidationError,
            SettingsError,
            FavoritesError,
            RecentHistoryError,
        ) as exc:
            self.logger.exception(
                "Technique data could not be loaded.",
                extra={
                    "event": "repository_reload_failed",
                    "error": str(exc),
                },
            )
            self._reset_loaded_data_state()
            self._show_user_message(
                "warning",
                "Technique data could not be loaded. Check the application log for details.",
                timeout_ms=7000,
            )
            return
        except Exception as exc:
            self.logger.exception(
                "Unexpected repository reload failure.",
                extra={
                    "event": "repository_reload_failed_unexpected",
                    "error": str(exc),
                },
            )
            self._reset_loaded_data_state()
            self._show_user_message(
                "critical",
                "Technique data could not be loaded. Check the application log for details.",
                timeout_ms=7000,
            )
            return

    def _apply_filters(self, _value: str | None = None) -> None:
        """Refresh the visible technique collection for the active section and filters."""
        if self._filter_timer.isActive():
            self._filter_timer.stop()

        section = self.sidebar.current_section()
        source_techniques = self._techniques_for_active_section(section)
        active_category = self._category_for_active_section(section)
        criteria = TechniqueFilterCriteria(
            category_name=(
                ALL_TECHNIQUES_LABEL
                if section == SECTION_CATEGORIES
                else active_category
            ),
            search_text=self.target_toolbar.search_text(),
        )
        techniques = self.filter_service.filter(source_techniques, criteria)
        self._visible_techniques = list(techniques)

        previous_selection = self.current_technique.id if self.current_technique else None
        self.technique_list.set_techniques(techniques)
        self.technique_list.set_result_summary(
            visible_count=len(techniques),
            source_count=len(source_techniques),
            search_text=self.target_toolbar.search_text(),
            category_name="" if active_category == ALL_TECHNIQUES_LABEL else active_category,
        )
        self.technique_list.set_favorite_ids(self.favorites_service.all_ids())

        if previous_selection and self.technique_list.select_technique(previous_selection):
            return

        if techniques:
            self.technique_list.select_first()
            self._show_status(f"Showing {len(techniques)} technique(s).", 3000)
        else:
            self.current_technique = None
            self.detail_panel.clear()
            self._show_status("No matching techniques found.", 4000)
            self._sync_toolbar_state()

    def _schedule_filter_update(self, _value: str | None = None) -> None:
        """Debounce free-text filtering to keep typing responsive."""
        self._filter_timer.start()

    def _techniques_for_active_section(self, section: str) -> list[Technique]:
        if section == SECTION_FAVORITES:
            return self.repository.techniques_for_ids(self.favorites_service.all_ids())

        if section == SECTION_RECENT:
            return self.repository.techniques_for_ids(
                self.recent_history_service.all_ids(),
                preserve_order=True,
            )

        if section == SECTION_CATEGORIES:
            return self.repository.techniques_for_category(self.sidebar.current_category())

        if section in {SECTION_SETTINGS, SECTION_ABOUT}:
            return []

        return self.repository.all_techniques()

    def _category_for_active_section(self, section: str) -> str:
        if section == SECTION_CATEGORIES:
            return self.sidebar.current_category()
        return ALL_TECHNIQUES_LABEL

    def _handle_sidebar_section_change(self, section: str) -> None:
        if section == SECTION_SETTINGS:
            self._open_settings_dialog()
            self._restore_browsing_context()
            return

        if section == SECTION_ABOUT:
            self._open_about_dialog()
            self._restore_browsing_context()
            return

        self._remember_browsing_context(section)
        section_messages = {
            SECTION_ALL: "Showing all techniques.",
            SECTION_FAVORITES: "Showing favorite techniques.",
            SECTION_RECENT: "Showing recently viewed techniques.",
            SECTION_CATEGORIES: f"Filtered by category: {self.sidebar.current_category()}",
        }
        if section in {SECTION_ALL, SECTION_FAVORITES, SECTION_RECENT}:
            self.target_toolbar.set_current_category(ALL_TECHNIQUES_LABEL)
        elif section == SECTION_CATEGORIES:
            self.target_toolbar.set_current_category(self.sidebar.current_category())
        self._show_status(section_messages.get(section, "Ready"), 4000)
        self._apply_filters(section)

    def _handle_toolbar_category_change(self, category_name: str) -> None:
        if category_name == ALL_TECHNIQUES_LABEL:
            self.sidebar.select_all()
            return

        self.sidebar.select_category(category_name)

    def _handle_technique_selected(self, technique_id: str) -> None:
        technique = self.repository.get(technique_id)
        if technique is None:
            self.logger.warning("Technique '%s' was selected but could not be found.", technique_id)
            self.current_technique = None
            self.detail_panel.clear()
            self._sync_toolbar_state()
            self._show_status("The selected technique could not be loaded.", 5000)
            return

        previous_technique_id = (
            self.current_technique.id if self.current_technique is not None else None
        )
        self.current_technique = technique
        if technique.id != previous_technique_id:
            try:
                self.recent_history_service.record_view(technique.id)
            except RecentHistoryError as exc:
                self.logger.exception(
                    "Recent history update failed.",
                    extra={
                        "event": "recent_history_update_failed",
                        "technique_id": technique.id,
                        "error": str(exc),
                    },
                )
                self._show_status("Recent history could not be updated.", 4000)
        self._refresh_detail_panel()
        self._show_status(f"Selected: {technique.name}", 4000)
        self._sync_toolbar_state()

    def _refresh_detail_panel(self, _value: str | None = None) -> None:
        """Rebuild the detail panel state for the current selection and target input."""
        if self.current_technique is None:
            self.detail_panel.clear()
            self._sync_toolbar_state()
            return

        detail_state = self._build_detail_state(
            self.current_technique,
            self.target_toolbar.target_text(),
        )
        self.detail_panel.set_detail(detail_state)
        self._sync_toolbar_state()

    def _copy_current_query(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a technique before copying.", 4000)
            return

        try:
            copy_result = self.clipboard_service.build_copy_result(
                self.current_technique,
                self.target_toolbar.target_text(),
            )
            QApplication.clipboard().setText(copy_result.text)
        except Exception as exc:
            self.logger.exception(
                "Clipboard copy failed.",
                extra={
                    "event": "clipboard_copy_failed",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "The query could not be copied right now.",
                timeout_ms=5000,
            )
            return

        self._show_status(copy_result.feedback_message, 5000)

    def _handle_copy_shortcut(self) -> None:
        if self._forward_copy_to_focused_text_widget():
            return
        self._copy_current_query()

    def _launch_current_technique(self) -> None:
        if self.current_technique is None:
            self._show_user_message(
                "information",
                "Select a technique before launching.",
                timeout_ms=4000,
            )
            return

        target = self.target_toolbar.target_text()
        if not target.strip():
            self._show_user_message(
                "warning",
                "Enter a target before launching a technique.",
                timeout_ms=5000,
            )
            return

        try:
            url = self.launcher.launch(
                self.current_technique,
                target,
                open_behavior=self.settings_service.settings.open_in_browser_behavior,
            )
        except QueryRenderError as exc:
            self.logger.exception(
                "Technique query rendering failed during launch.",
                extra={
                    "event": "technique_launch_render_failed",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "This technique could not be rendered with the current target input.",
                timeout_ms=6000,
            )
            return
        except BrowserIntegrationError as exc:
            self.logger.exception(
                "Browser launch failed.",
                extra={
                    "event": "technique_launch_browser_failed",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "DorkVault could not open the default browser.",
                timeout_ms=6000,
            )
            return
        except ValueError as exc:
            self.logger.warning(
                "Technique launch was blocked by invalid user input.",
                extra={
                    "event": "technique_launch_invalid_input",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                str(exc),
                timeout_ms=5000,
            )
            return
        except Exception as exc:
            self.logger.exception(
                "Technique launch failed unexpectedly.",
                extra={
                    "event": "technique_launch_failed_unexpected",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "critical",
                "The technique could not be launched. Check the application log for details.",
                timeout_ms=7000,
            )
            return

        try:
            self.settings_service.update_last_target(target)
        except SettingsError as exc:
            self.logger.exception(
                "Last target could not be saved after launch.",
                extra={
                    "event": "last_target_save_failed",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_status("Launched, but the last target could not be saved.", 6000)
        self._show_status(f"Launched in browser: {url}", 8000)
        self._sync_toolbar_state()

    def _handle_open_shortcut(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a technique before opening it in the browser.", 4000)
            return
        self._launch_current_technique()

    def _toggle_favorite(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a technique before updating favorites.", 4000)
            return

        try:
            is_favorite = self.favorites_service.toggle(self.current_technique.id)
        except (FavoritesError, ValueError) as exc:
            self.logger.exception(
                "Favorite update failed.",
                extra={
                    "event": "favorite_toggle_failed",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "Favorites could not be updated right now.",
                timeout_ms=5000,
            )
            return
        self.detail_panel.set_favorite_state(is_favorite)
        message = "Added to favorites" if is_favorite else "Removed from favorites"
        self._show_status(f"{message}: {self.current_technique.name}", 5000)
        self._apply_filters()
        self._sync_toolbar_state()

    def _open_export_dialog(self) -> None:
        """Open the export chooser and delegate to the selected export action."""
        export_options = self._available_export_options()
        if not export_options:
            self._show_status("Nothing is available to export right now.", 4000)
            return

        option_labels = [label for label, _value in export_options]
        selected_label, accepted = QInputDialog.getItem(
            self,
            "Export",
            "Choose what to export:",
            option_labels,
            0,
            False,
        )
        if not accepted:
            self._show_status("Export cancelled.", 3000)
            return

        option_lookup = {label: value for label, value in export_options}
        selected_option = option_lookup.get(selected_label, "")
        if selected_option == "rendered_query_txt":
            self._export_rendered_query_text()
            return
        if selected_option == "selected_technique_json":
            self._export_technique_collection_json(
                techniques=[self.current_technique] if self.current_technique is not None else [],
                default_file_name=(
                    f"{self.current_technique.id}_technique.json"
                    if self.current_technique
                    else "techniques.json"
                ),
                export_name="selected_technique",
            )
            return
        if selected_option == "visible_techniques_json":
            self._export_technique_collection_json(
                techniques=self._visible_techniques,
                default_file_name="visible_techniques.json",
                export_name="visible_techniques",
            )
            return
        if selected_option == "favorites_json":
            self._export_favorites_json()

    def _available_export_options(self) -> list[tuple[str, str]]:
        options: list[tuple[str, str]] = []
        if self.current_technique is not None:
            options.append(("Rendered Query (.txt)", "rendered_query_txt"))
            options.append(("Selected Technique (.json)", "selected_technique_json"))
        if self._visible_techniques:
            options.append(("Visible Techniques (.json)", "visible_techniques_json"))
        favorite_techniques = self._favorite_techniques()
        if favorite_techniques:
            options.append(("Favorites List (.json)", "favorites_json"))
        return options

    def _favorite_techniques(self) -> list[Technique]:
        """Return favorited techniques in the same stable order used elsewhere in the UI."""
        favorite_ids = set(self.favorites_service.all_ids())
        favorites = [
            technique
            for technique in self.repository.all_techniques()
            if technique.id in favorite_ids
        ]
        favorites.sort(key=lambda item: item.name.lower())
        return favorites

    def _export_rendered_query_text(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a technique before exporting a rendered query.", 4000)
            return

        try:
            rendered_query = self._render_current_query()
        except ValueError as exc:
            self.logger.warning(
                "Rendered query export was blocked by invalid input.",
                extra={
                    "event": "rendered_query_export_invalid_input",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message("warning", str(exc), timeout_ms=5000)
            return

        default_file_name = f"{self.current_technique.id}_query.txt"
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Rendered Query",
            str(Path.home() / default_file_name),
            "Text Files (*.txt)",
        )
        if not file_path:
            return

        try:
            self.export_service.export_rendered_query_text(Path(file_path), rendered_query)
        except ExportError as exc:
            self.logger.exception(
                "Rendered query export failed.",
                extra={
                    "event": "rendered_query_export_failed_ui",
                    "technique_id": self.current_technique.id,
                    "file_path": file_path,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "The rendered query could not be exported.",
                timeout_ms=6000,
            )
            return
        except ValueError as exc:
            self.logger.warning(
                "Rendered query export was rejected.",
                extra={
                    "event": "rendered_query_export_rejected",
                    "technique_id": self.current_technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message("warning", str(exc), timeout_ms=5000)
            return

        self._show_status(f"Exported rendered query to {file_path}", 6000)

    def _export_technique_collection_json(
        self,
        *,
        techniques: list[Technique],
        default_file_name: str,
        export_name: str,
    ) -> None:
        if not techniques:
            self._show_status("No techniques are available to export.", 4000)
            return

        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Techniques",
            str(Path.home() / default_file_name),
            "JSON Files (*.json)",
        )
        if not file_path:
            return

        try:
            self.export_service.export_techniques_json(
                Path(file_path),
                techniques,
                export_name=export_name,
            )
        except ExportError as exc:
            self.logger.exception(
                "Technique collection export failed.",
                extra={
                    "event": "technique_collection_export_failed_ui",
                    "file_path": file_path,
                    "export_name": export_name,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "The selected techniques could not be exported.",
                timeout_ms=6000,
            )
            return
        except ValueError as exc:
            self.logger.warning(
                "Technique collection export was rejected.",
                extra={
                    "event": "technique_collection_export_rejected",
                    "export_name": export_name,
                    "error": str(exc),
                },
            )
            self._show_user_message("warning", str(exc), timeout_ms=5000)
            return

        self._show_status(f"Exported {len(techniques)} technique(s) to {file_path}", 6000)

    def _export_favorites_json(self) -> None:
        favorite_techniques = self._favorite_techniques()
        if not favorite_techniques:
            self._show_status("No favorites are available to export.", 4000)
            return

        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Favorites",
            str(Path.home() / "favorite_techniques.json"),
            "JSON Files (*.json)",
        )
        if not file_path:
            return

        try:
            self.export_service.export_favorites_json(Path(file_path), favorite_techniques)
        except ExportError as exc:
            self.logger.exception(
                "Favorites export failed.",
                extra={
                    "event": "favorites_export_failed_ui",
                    "file_path": file_path,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "Favorites could not be exported.",
                timeout_ms=6000,
            )
            return
        except ValueError as exc:
            self.logger.warning(
                "Favorites export was rejected.",
                extra={
                    "event": "favorites_export_rejected",
                    "error": str(exc),
                },
            )
            self._show_user_message("warning", str(exc), timeout_ms=5000)
            return

        self._show_status(f"Exported favorites to {file_path}", 6000)

    def _render_current_query(self) -> str:
        if self.current_technique is None:
            raise ValueError("Select a technique first.")
        try:
            return self.current_technique.build_query(self.target_toolbar.target_text())
        except (QueryRenderError, ValueError) as exc:
            raise ValueError(str(exc)) from exc

    def _build_detail_state(self, technique: Technique, target: str) -> TechniqueDetailState:
        preview_state = self.preview_service.build_preview(technique, target)
        tags_text = ", ".join(technique.tags) if technique.tags else "None"
        required_names = [variable.name for variable in technique.required_variables]
        required_variables_text = ", ".join(required_names) if required_names else "None"
        is_favorite = self.favorites_service.is_favorite(technique.id)

        return TechniqueDetailState(
            technique=technique,
            tags_text=tags_text,
            required_variables_text=required_variables_text,
            preview_query=preview_state.preview_query,
            preview_status=preview_state.status_text,
            is_favorite=is_favorite,
            can_manage_custom=self.custom_technique_service.is_custom_technique(technique),
        )

    def _show_status(self, message: str, timeout_ms: int = 4000) -> None:
        self.statusBar().showMessage(message, timeout_ms)

    def _show_user_message(self, level: str, message: str, *, timeout_ms: int = 5000) -> None:
        self._show_status(message, timeout_ms)
        if level == "critical":
            QMessageBox.critical(self, APP_NAME, message)
            return
        if level == "information":
            QMessageBox.information(self, APP_NAME, message)
            return
        QMessageBox.warning(self, APP_NAME, message)

    def _reset_loaded_data_state(self) -> None:
        """Clear UI state after a startup or reload failure."""
        self._visible_techniques = []
        self.sidebar.set_category_groups([], {ALL_TECHNIQUES_LABEL: 0})
        self.target_toolbar.set_categories([])
        self.target_toolbar.set_current_category(ALL_TECHNIQUES_LABEL)
        self.technique_list.set_techniques([])
        self.technique_list.set_result_summary(visible_count=0, source_count=0)
        self.detail_panel.clear()
        self.current_technique = None
        self._sync_toolbar_state()

    def _focus_search(self) -> None:
        self.target_toolbar.focus_search_input()

    def _focus_target(self) -> None:
        self.target_toolbar.focus_target_input()

    def _handle_export_shortcut(self) -> None:
        self._open_export_dialog()

    def _forward_copy_to_focused_text_widget(self) -> bool:
        """Preserve normal text-copy behavior when the user is inside a text field."""
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            if focused_widget.hasSelectedText():
                focused_widget.copy()
                return True
            return False

        if isinstance(focused_widget, QPlainTextEdit):
            if focused_widget.textCursor().hasSelection():
                focused_widget.copy()
                return True
            return False

        return False

    def _remember_browsing_context(self, section: str) -> None:
        if section not in {SECTION_ALL, SECTION_FAVORITES, SECTION_RECENT, SECTION_CATEGORIES}:
            return
        self._last_browsing_section = section
        self._last_browsing_category = self.sidebar.current_category()

    def _restore_browsing_context(self) -> None:
        if (
            self._last_browsing_section == SECTION_CATEGORIES
            and self._last_browsing_category != ALL_TECHNIQUES_LABEL
        ):
            self.sidebar.select_category(self._last_browsing_category)
            return
        self.sidebar.set_section(self._last_browsing_section)

    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.settings_service, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            self._show_status("Settings unchanged.", 3000)
            return

        updated_settings = dialog.selected_settings()
        try:
            self.settings_service.update(updated_settings)
        except SettingsError as exc:
            self.logger.exception(
                "Settings update failed from the dialog.",
                extra={
                    "event": "settings_update_failed_ui",
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "Settings could not be saved.",
                timeout_ms=6000,
            )
            return
        self._apply_settings_to_runtime(updated_settings)
        self._show_status("Settings saved.", 4000)

    def _open_about_dialog(self) -> None:
        """Show a small About dialog without disrupting the browsing workflow."""
        technique_count = len(self.repository.all_techniques())
        QMessageBox.information(
            self,
            APP_NAME,
            (
                f"{APP_NAME} {APP_VERSION}\n\n"
                "Local desktop launcher for search-based recon techniques used during "
                "authorized security research.\n\n"
                f"Loaded techniques: {technique_count}\n"
                "Data source: bundled JSON catalogs plus optional user custom techniques.\n\n"
                "What DorkVault cannot do:\n"
                "- It does not perform active scanning or exploitation.\n"
                "- It does not verify findings or guarantee search engine results.\n"
                "- It does not bypass authentication or collect secrets automatically.\n"
                "- It depends on external engines such as Google, GitHub, Wayback, "
                "Shodan, and Censys.\n"
                "- It cannot ensure authorization, legality, or pack freshness for the user."
            ),
        )
        self._show_status("About DorkVault", 4000)

    def _editable_category_names(self) -> list[str]:
        """Return category names suitable for create/edit dialogs."""
        return [name for name in self.repository.category_names() if name != ALL_TECHNIQUES_LABEL]

    def _open_custom_technique_editor(
        self,
        existing_technique: Technique | None = None,
    ) -> Technique | None:
        """Open the custom-technique editor and return the saved technique when accepted."""
        dialog = CustomTechniqueDialog(
            self.custom_technique_service,
            category_names=self._editable_category_names(),
            engine_names=self.repository.engine_names(),
            existing_ids=[technique.id for technique in self.repository.all_techniques()],
            existing_technique=existing_technique,
            parent=self,
        )
        if (
            dialog.exec() != CustomTechniqueDialog.DialogCode.Accepted
            or dialog.saved_technique is None
        ):
            return None
        return dialog.saved_technique

    def _create_custom_technique(self) -> None:
        created_technique = self._open_custom_technique_editor()
        if created_technique is None:
            self._show_status("Custom technique creation cancelled.", 3000)
            return
        self._reload_repository(selected_technique_id=created_technique.id)
        self._show_status(f"Created custom technique: {created_technique.name}", 5000)

    def _edit_current_custom_technique(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a custom technique before editing.", 4000)
            return
        if not self.custom_technique_service.is_custom_technique(self.current_technique):
            self._show_status("Built-in techniques cannot be edited directly.", 5000)
            return

        saved_technique = self._open_custom_technique_editor(self.current_technique)
        if saved_technique is None:
            self._show_status("Custom technique edit cancelled.", 3000)
            return

        self._reload_repository(selected_technique_id=saved_technique.id)
        self._show_status(f"Updated custom technique: {saved_technique.name}", 5000)

    def _delete_current_custom_technique(self) -> None:
        if self.current_technique is None:
            self._show_status("Select a custom technique before deleting.", 4000)
            return
        if not self.custom_technique_service.is_custom_technique(self.current_technique):
            self._show_status("Built-in techniques cannot be deleted.", 5000)
            return

        technique = self.current_technique
        confirm = QMessageBox.question(
            self,
            APP_NAME,
            f"Delete the custom technique '{technique.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            self._show_status("Custom technique deletion cancelled.", 3000)
            return

        try:
            self.custom_technique_service.delete_custom_technique(technique.id)
        except (CustomTechniqueError, ValueError) as exc:
            self.logger.exception(
                "Custom technique deletion failed.",
                extra={
                    "event": "custom_technique_delete_failed_ui",
                    "technique_id": technique.id,
                    "error": str(exc),
                },
            )
            self._show_user_message(
                "warning",
                "The custom technique could not be deleted.",
                timeout_ms=6000,
            )
            return

        try:
            self.favorites_service.remove(technique.id)
        except FavoritesError:
            self.logger.exception(
                "Favorite cleanup failed after deleting a custom technique.",
                extra={
                    "event": "custom_technique_favorite_cleanup_failed",
                    "technique_id": technique.id,
                },
            )
        try:
            self.recent_history_service.remove(technique.id)
        except RecentHistoryError:
            self.logger.exception(
                "Recent history cleanup failed after deleting a custom technique.",
                extra={
                    "event": "custom_technique_recent_cleanup_failed",
                    "technique_id": technique.id,
                },
            )
        self.current_technique = None
        self._reload_repository()
        self._show_status(f"Deleted custom technique: {technique.name}", 5000)

    def _focus_technique(self, technique_id: str) -> None:
        self._apply_filters()
        if self.technique_list.model.index_for_technique_id(technique_id).isValid():
            self.technique_list.select_technique(technique_id)
            return

        self.target_toolbar.set_search_text("")
        self.sidebar.select_all()
        self.target_toolbar.set_current_category(ALL_TECHNIQUES_LABEL)
        self._apply_filters()
        if self.technique_list.model.index_for_technique_id(technique_id).isValid():
            self.technique_list.select_technique(technique_id)

    def _apply_settings_to_runtime(self, settings: AppSettings) -> None:
        self.recent_history_service.max_items = settings.recent_limit
        try:
            self.recent_history_service.save(self.recent_history_service.all_ids())
        except RecentHistoryError as exc:
            self.logger.exception(
                "Recent history could not be trimmed after settings were applied.",
                extra={
                    "event": "recent_history_trim_failed",
                    "error": str(exc),
                    "recent_limit": settings.recent_limit,
                },
            )
            self._show_status("Recent history could not be updated to the new limit.", 5000)
        self.technique_list.set_compact_view_enabled(settings.compact_view_enabled)

        application = QApplication.instance()
        if application is not None:
            settings.theme = self.theme_manager.apply_theme(application, settings.theme)

    def _sync_toolbar_state(self) -> None:
        self.target_toolbar.set_action_state(
            can_export=bool(self._available_export_options()),
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            self.settings_service.settings.last_target = self.target_toolbar.target_text().strip()
            self.settings_service.settings.window_geometry = self._serialized_window_geometry()
            self.settings_service.save()
        except SettingsError as exc:
            self.logger.exception(
                "Window state could not be saved during shutdown.",
                extra={
                    "event": "shutdown_window_state_save_failed",
                    "error": str(exc),
                },
            )
        super().closeEvent(event)
