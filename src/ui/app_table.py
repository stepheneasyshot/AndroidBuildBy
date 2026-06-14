from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import AppInfo


class AppTable(QWidget):
    app_selected = Signal(str)

    COL_NAME = 0
    COL_PACKAGE = 1
    COL_VERSION = 2
    COL_SYSTEM = 3

    def __init__(self):
        super().__init__()
        self._apps: list[AppInfo] = []
        self._filtered_apps: list[AppInfo] = []
        self._user_only = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 8)

        # Search & filter bar
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search apps...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)

        self.check_user_only = QCheckBox("User apps only")
        self.check_user_only.setChecked(True)
        self.check_user_only.toggled.connect(self._on_user_only_changed)

        filter_layout.addWidget(self.search_input, stretch=1)
        filter_layout.addWidget(self.check_user_only)
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["App Name", "Package", "Version", "Type"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_PACKAGE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_VERSION, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_SYSTEM, QHeaderView.ResizeMode.Interactive)

        self.table.currentCellChanged.connect(lambda row, *_: self._on_row_changed(row))
        layout.addWidget(self.table)

    def set_apps(self, apps: list[AppInfo]):
        self._apps = apps
        self._apply_filter()

    def add_apps(self, apps: list[AppInfo]):
        self._apps.extend(apps)
        self._apply_filter()

    def get_app_by_package(self, package: str) -> AppInfo | None:
        for app in self._apps:
            if app.package_name == package:
                return app
        return None

    def selected_package(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, self.COL_PACKAGE)
        return item.text() if item else None

    def _on_user_only_changed(self, checked: bool):
        self._user_only = checked
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        self._filtered_apps = []
        for app in self._apps:
            if self._user_only and app.is_system:
                continue
            if query:
                searchable = f"{app.app_name} {app.package_name}".lower()
                if query not in searchable:
                    continue
            self._filtered_apps.append(app)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._filtered_apps))
        for i, app in enumerate(self._filtered_apps):
            self.table.setItem(i, self.COL_NAME, QTableWidgetItem(app.display_name))
            self.table.setItem(i, self.COL_PACKAGE, QTableWidgetItem(app.package_name))
            self.table.setItem(i, self.COL_VERSION, QTableWidgetItem(app.version_display))
            type_item = QTableWidgetItem("System" if app.is_system else "User")
            self.table.setItem(i, self.COL_SYSTEM, type_item)

        # Distribute width: name 40%, package 40%, version 10%, type 10%
        vp_w = self.table.viewport().width()
        if vp_w > 0:
            self.table.setColumnWidth(self.COL_NAME, int(vp_w * 0.20))
            self.table.setColumnWidth(self.COL_PACKAGE, int(vp_w * 0.40))
            self.table.setColumnWidth(self.COL_VERSION, int(vp_w * 0.20))
            self.table.setColumnWidth(self.COL_SYSTEM, int(vp_w * 0.20))

    def _on_row_changed(self, row: int):
        if 0 <= row < len(self._filtered_apps):
            self.app_selected.emit(self._filtered_apps[row].package_name)
