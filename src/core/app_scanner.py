from __future__ import annotations

import logging
import re

from ..models import AppInfo
from .adb_wrapper import ADBWrapper, ADBError

logger = logging.getLogger(__name__)


class AppScanner:
    def __init__(self, adb: ADBWrapper, device_serial: str = ""):
        self.adb = adb
        self.device_serial = device_serial

    def scan_installed_apps(self, user_only: bool = True) -> list[AppInfo]:
        packages = self.adb.get_installed_packages(device=self.device_serial, user_only=False)
        system_packages = self.adb.get_system_packages(device=self.device_serial)
        apps: list[AppInfo] = []

        for pkg in packages:
            try:
                app = self._get_app_info(pkg, system_packages)
                if user_only and app.is_system:
                    continue
                apps.append(app)
            except ADBError:
                logger.debug("Skipping %s: failed to get info", pkg)
                apps.append(AppInfo(package_name=pkg, is_system=(pkg in system_packages)))

        apps.sort(key=lambda a: (a.is_system, a.display_name.lower()))
        return apps

    def _get_app_info(self, package: str, system_packages: set[str]) -> AppInfo:
        info = self.adb.get_package_info(package, device=self.device_serial)
        app_name = self._resolve_app_name(package)

        version_code = 0
        if vc := info.get("version_code"):
            try:
                version_code = int(vc)
            except ValueError:
                pass

        target_sdk = 0
        if ts := info.get("target_sdk"):
            try:
                target_sdk = int(ts)
            except ValueError:
                pass

        return AppInfo(
            package_name=package,
            app_name=app_name or package,
            version_name=info.get("version_name", ""),
            version_code=version_code,
            is_system=(package in system_packages),
            install_time=info.get("install_time", ""),
            target_sdk=target_sdk,
            min_sdk=self._get_min_sdk(package),
            apk_path=info.get("apk_path", ""),
        )

    def _resolve_app_name(self, package: str) -> str:
        try:
            output = self.adb.shell(
                f"pm dump {package} | grep -A5 'Activity Resolver'",
                device=self.device_serial,
            )
        except ADBError:
            return package
        return package

    def _get_min_sdk(self, package: str) -> int:
        try:
            output = self.adb.shell(
                f"dumpsys package {package} | grep 'minSdk'",
                device=self.device_serial,
            )
            match = re.search(r"minSdk=(\d+)", output)
            if match:
                return int(match.group(1))
        except ADBError:
            pass
        return 0
