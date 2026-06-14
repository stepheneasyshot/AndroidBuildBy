from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..models import AppInfo, AnalysisResult
from ..utils.android_versions import sdk_to_version
from .workers import AnalyzeAPKWorker

DARK_BG = "#1E1E1E"
DARK_SURFACE = "#2D2D2D"
DARK_TEXT = "#E0E0E0"
DARK_TEXT_SECONDARY = "#A0A0A0"
DARK_BORDER = "#404040"
DARK_ACCENT = "#64B5F6"
DARK_SUCCESS = "#81C784"

# Inline dark stylesheet for this widget and children
DARK_STYLE = f"""
    AnalysisView {{
        background-color: {DARK_BG};
    }}
    AnalysisView QWidget {{
        color: {DARK_TEXT};
        background-color: transparent;
    }}
    AnalysisView QGroupBox {{
        font-weight: bold;
        border: 1px solid {DARK_BORDER};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 16px;
        color: {DARK_TEXT};
    }}
    AnalysisView QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {DARK_ACCENT};
    }}
    AnalysisView QLabel {{
        color: {DARK_TEXT};
    }}
    AnalysisView QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    AnalysisView QProgressBar {{
        border: 1px solid {DARK_BORDER};
        border-radius: 4px;
        text-align: center;
        background-color: {DARK_SURFACE};
        color: {DARK_TEXT};
        height: 20px;
    }}
    AnalysisView QProgressBar::chunk {{
        background-color: {DARK_ACCENT};
        border-radius: 3px;
    }}
"""

KEY_LABEL_STYLE = f"font-weight: bold; min-width: 110px; color: {DARK_TEXT_SECONDARY};"
VAL_LABEL_STYLE = f"color: {DARK_TEXT};"
SEPARATOR_STYLE = f"border: none; border-top: 1px solid {DARK_BORDER}; margin: 8px 0;"


class _SectionTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(f"color: {DARK_ACCENT}; font-weight: bold; font-size: 14px;")


class AnalysisView(QWidget):
    @property
    def current_result(self) -> AnalysisResult | None:
        return self._current_result

    def __init__(self):
        super().__init__()
        self.setStyleSheet(DARK_STYLE)
        self._analyze_worker: AnalyzeAPKWorker | None = None
        self._current_result: AnalysisResult | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)

        # Placeholder
        self._placeholder = QLabel("Select an app and click Analyze to view details")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"color: {DARK_TEXT_SECONDARY}; font-size: 16px; padding: 40px;")
        self._content_layout.addWidget(self._placeholder)

        # App basic info section
        self._section_title = _SectionTitle("")
        self._section_title.setVisible(False)
        self._content_layout.addWidget(self._section_title)

        self._info_box = QGroupBox("Basic Info")
        self._info_box.setVisible(False)
        box_layout = QVBoxLayout(self._info_box)
        self._info_labels: dict[str, QLabel] = {}
        for key in ("App Name", "Package", "Version", "Install Time"):
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setStyleSheet(KEY_LABEL_STYLE)
            v = QLabel("-")
            v.setWordWrap(True)
            v.setStyleSheet(VAL_LABEL_STYLE)
            row.addWidget(k)
            row.addWidget(v, stretch=1)
            box_layout.addLayout(row)
            self._info_labels[key] = v
        self._content_layout.addWidget(self._info_box)

        # Platform & SDK
        self._platform_box = QGroupBox("Platform & SDK")
        self._platform_box.setVisible(False)
        plat_layout = QVBoxLayout(self._platform_box)
        self._platform_labels: dict[str, QLabel] = {}
        for key in ("Platform", "Min SDK", "Target SDK", "Supported ABIs"):
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setStyleSheet(KEY_LABEL_STYLE)
            v = QLabel("-")
            v.setWordWrap(True)
            v.setStyleSheet(VAL_LABEL_STYLE)
            row.addWidget(k)
            row.addWidget(v, stretch=1)
            plat_layout.addLayout(row)
            self._platform_labels[key] = v
        self._content_layout.addWidget(self._platform_box)

        # Separator
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.Shape.HLine)
        self._sep.setStyleSheet(SEPARATOR_STYLE)
        self._sep.setVisible(False)
        self._content_layout.addWidget(self._sep)

        # Native libraries
        self._libs_box = QGroupBox("Native Libraries")
        self._libs_box.setVisible(False)
        libs_layout = QVBoxLayout(self._libs_box)
        self._libs_label = QLabel("-")
        self._libs_label.setWordWrap(True)
        self._libs_label.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {DARK_TEXT};")
        libs_layout.addWidget(self._libs_label)
        self._content_layout.addWidget(self._libs_box)

        # Detected SDKs
        self._sdks_box = QGroupBox("Detected SDKs")
        self._sdks_box.setVisible(False)
        sdks_layout = QVBoxLayout(self._sdks_box)
        self._sdks_label = QLabel("-")
        self._sdks_label.setWordWrap(True)
        self._sdks_label.setStyleSheet(f"color: {DARK_TEXT};")
        sdks_layout.addWidget(self._sdks_label)
        self._content_layout.addWidget(self._sdks_box)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._content_layout.addWidget(self._progress)

        self._content_layout.addStretch()
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def show_basic_info(self, app: AppInfo):
        self._placeholder.setVisible(False)
        self._section_title.setVisible(True)
        self._section_title.setText(app.display_name)

        self._info_box.setVisible(True)
        self._info_labels["App Name"].setText(app.display_name)
        self._info_labels["Package"].setText(app.package_name)
        self._info_labels["Version"].setText(app.version_display)
        self._info_labels["Install Time"].setText(app.install_time or "-")

        self._platform_box.setVisible(True)
        min_ver = sdk_to_version(app.min_sdk) if app.min_sdk else "-"
        target_ver = sdk_to_version(app.target_sdk) if app.target_sdk else "-"
        self._platform_labels["Min SDK"].setText(f"API {app.min_sdk}  ({min_ver})" if app.min_sdk else "-")
        self._platform_labels["Target SDK"].setText(f"API {app.target_sdk}  ({target_ver})" if app.target_sdk else "-")
        self._platform_labels["Supported ABIs"].setText("-")

        self._sep.setVisible(False)
        self._libs_box.setVisible(False)
        self._sdks_box.setVisible(False)

    def start_analysis(self, package: str, device_manager):
        if self._analyze_worker and self._analyze_worker.isRunning():
            self._analyze_worker.quit()
            self._analyze_worker.wait()

        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        self._analyze_worker = AnalyzeAPKWorker(package, device_manager)
        self._analyze_worker.finished.connect(self._on_analysis_finished)
        self._analyze_worker.error.connect(self._on_analysis_error)
        self._analyze_worker.start()

    def _on_analysis_finished(self, result: AnalysisResult):
        self._progress.setVisible(False)
        self._current_result = result
        self._display_result(result)

    def _on_analysis_error(self, message: str):
        self._progress.setVisible(False)
        QMessageBox.warning(self, "Analysis Error", message)

    def _display_result(self, r: AnalysisResult):
        self._section_title.setText(f"{r.app_name or r.package_name}  —  {r.platform.value}")

        # Platform
        self._platform_box.setVisible(True)
        self._platform_labels["Platform"].setText(r.platform.value)
        meta = r.tech_metadata
        min_ver = sdk_to_version(meta.min_sdk) if meta.min_sdk else "-"
        target_ver = sdk_to_version(meta.target_sdk) if meta.target_sdk else "-"
        self._platform_labels["Min SDK"].setText(f"API {meta.min_sdk}  ({min_ver})" if meta.min_sdk else "-")
        self._platform_labels["Target SDK"].setText(f"API {meta.target_sdk}  ({target_ver})" if meta.target_sdk else "-")
        self._platform_labels["Supported ABIs"].setText(", ".join(meta.supported_abis) if meta.supported_abis else "-")

        self._sep.setVisible(True)

        # Native libs
        if r.native_libs:
            self._libs_box.setVisible(True)
            self._libs_box.setTitle(f"Native Libraries ({len(r.native_libs)})")
            lines = [f"  {lib.name}  [{lib.abi}]" for lib in r.native_libs]
            self._libs_label.setText("\n".join(lines))
        else:
            self._libs_box.setVisible(False)

        # SDKs
        if r.detected_sdks:
            self._sdks_box.setVisible(True)
            self._sdks_box.setTitle(f"Detected SDKs ({len(r.detected_sdks)})")
            lines = [f"  {s.name}  ({s.category})" if s.category else f"  {s.name}" for s in r.detected_sdks]
            self._sdks_label.setText("\n".join(lines))
        else:
            self._sdks_box.setVisible(False)
