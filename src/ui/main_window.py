from __future__ import annotations

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..core.adb_wrapper import ADBNotFoundError
from ..core.device_manager import DeviceManager
from ..models import AppInfo
from .styles import (
    APP_NAME,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    LEFT_PANEL_WIDTH,
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
)
from .device_panel import DevicePanel
from .app_table import AppTable
from .analysis_view import AnalysisView
from .workers import ScanAppsWorker, ExtractAPKWorker, ExportReportWorker

logger = logging.getLogger(__name__)

BUTTON_BAR_STYLE = f"""
    QWidget#buttonBar {{
        background-color: {COLOR_SURFACE};
        border-bottom: 1px solid {COLOR_BORDER};
    }}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)

        self.device_manager = DeviceManager()
        self._scan_worker: ScanAppsWorker | None = None
        self._extract_worker: ExtractAPKWorker | None = None
        self._export_worker: ExportReportWorker | None = None

        self._setup_ui()
        self._connect_signals()
        self._initial_check()

    def _setup_ui(self):
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Button bar (replaces QToolBar)
        button_bar = QWidget(objectName="buttonBar")
        button_bar.setStyleSheet(BUTTON_BAR_STYLE)
        bar_layout = QHBoxLayout(button_bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.setSpacing(8)

        bar_layout.addWidget(QLabel(APP_NAME, styleSheet="font-weight: bold; font-size: 15px;"))
        bar_layout.addStretch()

        self.btn_refresh = QPushButton("Refresh Device")
        self.btn_analyze = QPushButton("Analyze")
        self.btn_backup = QPushButton("Backup APK")
        self.btn_export = QPushButton("Export Report")

        self.btn_analyze.setEnabled(False)
        self.btn_backup.setEnabled(False)
        self.btn_export.setEnabled(False)

        bar_layout.addWidget(self.btn_refresh)
        bar_layout.addWidget(self.btn_analyze)
        bar_layout.addWidget(self.btn_backup)
        bar_layout.addWidget(self.btn_export)

        central_layout.addWidget(button_bar)

        # Main content: splitter with left/right panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.device_panel = DevicePanel()
        self.app_table = AppTable()
        left_layout.addWidget(self.device_panel)
        left_layout.addWidget(self.app_table, stretch=1)
        left_widget.setMinimumWidth(LEFT_PANEL_WIDTH)

        # Right panel (dark theme)
        self.analysis_view = AnalysisView()

        splitter.addWidget(left_widget)
        splitter.addWidget(self.analysis_view)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        central_layout.addWidget(splitter, stretch=1)
        self.setCentralWidget(central)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        self.btn_refresh.clicked.connect(self._on_refresh_device)
        self.btn_analyze.clicked.connect(self._on_analyze)
        self.btn_backup.clicked.connect(self._on_backup)
        self.btn_export.clicked.connect(self._on_export)
        self.device_panel.device_selected.connect(self._on_device_selected)
        self.app_table.app_selected.connect(self._on_app_selected)

    def _on_app_selected(self, package_name: str):
        self.btn_analyze.setEnabled(True)
        self.btn_backup.setEnabled(True)
        app_info = self.app_table.get_app_by_package(package_name)
        if app_info:
            self.analysis_view.show_basic_info(app_info)

    # --- remaining methods unchanged ---

    def _initial_check(self):
        if not self.device_manager.is_adb_available():
            QMessageBox.warning(
                self,
                "ADB Not Found",
                "Android Debug Bridge (adb) was not found in your PATH.\n\n"
                "Please install Android Platform Tools and add adb to your PATH.",
            )
            self.status_bar.showMessage("ADB not found - please install Android Platform Tools")
            return
        self._on_refresh_device()

    def _on_refresh_device(self):
        try:
            devices = self.device_manager.refresh_devices()
        except ADBNotFoundError:
            QMessageBox.warning(self, "ADB Not Found", "adb command not found. Please install Android Platform Tools.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to detect devices: {e}")
            return

        self.device_panel.update_devices(devices, self.device_manager.current_device)

        if not devices:
            self.status_bar.showMessage("No devices connected")
            return

        connected = [d for d in devices if d.is_connected]
        if not connected:
            self.status_bar.showMessage("Device connected but unauthorized - enable USB debugging")
            return

        self.status_bar.showMessage(f"Connected: {self.device_manager.current_device.display_name}")
        self._start_scan_apps()

    def _on_device_selected(self, serial: str):
        device = self.device_manager.select_device(serial)
        if device:
            self.status_bar.showMessage(f"Selected: {device.display_name}")
            self._start_scan_apps()

    def _start_scan_apps(self):
        if not self.device_manager.current_device:
            return
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.quit()
            self._scan_worker.wait()

        device = self.device_manager.current_device
        self.status_bar.showMessage(f"Scanning apps on {device.display_name} ({device.serial})...")
        self._scan_worker = ScanAppsWorker(
            self.device_manager.adb,
            self.device_manager.current_serial,
        )
        self._scan_worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
        self._scan_worker.partial_result.connect(self.app_table.add_apps)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_finished(self, apps):
        self.app_table.set_apps(apps)
        self.status_bar.showMessage(f"Found {len(apps)} apps")

    def _on_scan_error(self, message: str):
        self.status_bar.showMessage(f"Scan failed: {message}")
        QMessageBox.warning(self, "Scan Error", message)

    def _on_analyze(self):
        package = self.app_table.selected_package()
        if not package:
            return
        self.analysis_view.start_analysis(package, self.device_manager)

    def _on_backup(self):
        package = self.app_table.selected_package()
        if not package:
            return

        default_dir = os.path.expanduser("~/AndroidBuildBy/backups")
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Directory", default_dir
        )
        if not output_dir:
            return

        self.status_bar.showMessage(f"Backing up {package}...")
        self._extract_worker = ExtractAPKWorker(package, self.device_manager, output_dir)
        self._extract_worker.finished.connect(self._on_backup_finished)
        self._extract_worker.error.connect(self._on_backup_error)
        self._extract_worker.start()

    def _on_backup_finished(self, path: str):
        self.status_bar.showMessage(f"Backup saved: {path}")
        QMessageBox.information(self, "Backup Complete", f"APK saved to:\n{path}")

    def _on_backup_error(self, message: str):
        self.status_bar.showMessage(f"Backup failed: {message}")
        QMessageBox.warning(self, "Backup Error", message)

    def _on_export(self):
        result = self.analysis_view.current_result
        if not result:
            QMessageBox.information(self, "No Data", "Analyze an app first before exporting.")
            return

        path, filter_ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            f"{result.package_name}_report",
            "JSON (*.json);;CSV (*.csv);;Text (*.txt)",
        )
        if not path:
            return

        fmt = "json"
        if path.endswith(".csv"):
            fmt = "csv"
        elif path.endswith(".txt"):
            fmt = "text"

        self._export_worker = ExportReportWorker(result, path, fmt)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.error.connect(self._on_export_error)
        self._export_worker.start()

    def _on_export_finished(self, path: str):
        self.status_bar.showMessage(f"Report exported: {path}")

    def _on_export_error(self, message: str):
        self.status_bar.showMessage(f"Export failed: {message}")
        QMessageBox.warning(self, "Export Error", message)
