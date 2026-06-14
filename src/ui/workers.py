from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from ..core.adb_wrapper import ADBWrapper, ADBError
from ..core.device_manager import DeviceManager
from ..models import AppInfo, AnalysisResult

logger = logging.getLogger(__name__)


class ScanAppsWorker(QThread):
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(str)
    partial_result = Signal(list)  # emitted every N apps for real-time table update

    def __init__(self, adb: ADBWrapper, device_serial: str):
        super().__init__()
        self.adb = adb
        self.device_serial = device_serial

    def run(self):
        try:
            self.progress.emit("Fetching package list...")
            packages = self.adb.get_installed_packages(device=self.device_serial, user_only=False)
            total = len(packages)
            self.progress.emit(f"Found {total} packages, fetching details...")

            self.progress.emit("Fetching system package list...")
            system_packages = self.adb.get_system_packages(device=self.device_serial)
            self.progress.emit(f"System packages: {len(system_packages)}, user packages: {total - len(system_packages & set(packages))}")

            apps = []
            batch = []
            user_count = 0
            for i, pkg in enumerate(packages):
                is_sys = pkg in system_packages
                try:
                    info = self.adb.get_package_info(pkg, device=self.device_serial)
                    app = AppInfo(
                        package_name=pkg,
                        app_name=info.get("app_name", pkg),
                        version_name=info.get("version_name", ""),
                        version_code=int(info.get("version_code", "0") or "0"),
                        is_system=is_sys,
                        install_time=info.get("install_time", ""),
                        target_sdk=int(info.get("target_sdk", "0") or "0"),
                        min_sdk=int(info.get("min_sdk", "0") or "0"),
                        apk_path=info.get("apk_path", ""),
                    )
                    label_result = self.adb.shell(
                        f"dumpsys package {pkg} | grep -A1 'ApplicationInfo'",
                        device=self.device_serial,
                    )
                    if label_result:
                        app.app_name = pkg
                    apps.append(app)
                    batch.append(app)
                    if not is_sys:
                        user_count += 1
                except ADBError:
                    fallback = AppInfo(package_name=pkg, is_system=is_sys)
                    apps.append(fallback)
                    batch.append(fallback)

                if (i + 1) % 20 == 0 or i == total - 1:
                    self.progress.emit(f"Scanned {i + 1}/{total} apps ({user_count} user)")
                    self.partial_result.emit(batch)
                    batch = []

            apps.sort(key=lambda a: (a.is_system, a.display_name.lower()))
            self.progress.emit(f"Scan complete: {len(apps)} apps ({user_count} user)")
            self.finished.emit(apps)

        except ADBError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")


class AnalyzeAPKWorker(QThread):
    finished = Signal(object)  # AnalysisResult
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, package: str, device_manager: DeviceManager):
        super().__init__()
        self.package = package
        self.device_manager = device_manager

    def run(self):
        try:
            from ..core.apk_extractor import APKExtractor
            from ..core.apk_analyzer import APKAnalyzer

            self.progress.emit("Extracting APK...")
            extractor = APKExtractor(self.device_manager.adb, self.device_manager.current_serial)
            apk_path = extractor.extract(self.package)

            self.progress.emit("Analyzing APK...")
            analyzer = APKAnalyzer()
            result = analyzer.deep_analyze(apk_path)
            result.package_name = self.package

            self.finished.emit(result)

        except ADBError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Analysis failed")
            self.error.emit(f"Analysis failed: {e}")


class ExtractAPKWorker(QThread):
    finished = Signal(str)  # local path
    error = Signal(str)
    progress = Signal(int)  # percentage

    def __init__(self, package: str, device_manager: DeviceManager, output_dir: str):
        super().__init__()
        self.package = package
        self.device_manager = device_manager
        self.output_dir = output_dir

    def run(self):
        try:
            from ..core.apk_extractor import APKExtractor

            extractor = APKExtractor(self.device_manager.adb, self.device_manager.current_serial)
            path = extractor.extract(self.package, output_dir=self.output_dir)
            self.finished.emit(path)

        except ADBError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Extraction failed: {e}")


class ExportReportWorker(QThread):
    finished = Signal(str)  # output file path
    error = Signal(str)

    def __init__(self, result: AnalysisResult, output_path: str, format: str = "json"):
        super().__init__()
        self.result = result
        self.output_path = output_path
        self.format = format

    def run(self):
        try:
            from ..core.report_exporter import ReportExporter

            exporter = ReportExporter()
            if self.format == "json":
                exporter.to_json(self.result, self.output_path)
            elif self.format == "csv":
                exporter.to_csv(self.result, self.output_path)
            else:
                exporter.to_text(self.result, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))
