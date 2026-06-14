from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from .adb_wrapper import ADBWrapper, ADBError

logger = logging.getLogger(__name__)

DEFAULT_BACKUP_DIR = os.path.expanduser("~/AndroidBuildBy/backups")


class APKExtractor:
    def __init__(self, adb: ADBWrapper, device_serial: str = ""):
        self.adb = adb
        self.device_serial = device_serial

    def extract(self, package: str, output_dir: str = "") -> str:
        remote_path = self.adb.get_package_path(package, device=self.device_serial)
        if not remote_path:
            raise ADBError(f"Cannot find APK path for {package}")

        if not output_dir:
            output_dir = tempfile.mkdtemp(prefix="abb_")

        os.makedirs(output_dir, exist_ok=True)

        # Try to get version for filename
        info = self.adb.get_package_info(package, device=self.device_serial)
        version = info.get("version_name", "unknown")

        safe_name = package.replace(".", "_")
        filename = f"{safe_name}_{version}.apk"
        local_path = os.path.join(output_dir, filename)

        if os.path.exists(local_path):
            logger.info("APK already cached: %s", local_path)
            return local_path

        result = self.adb.pull_file(remote_path, local_path, device=self.device_serial)
        if not result.success:
            raise ADBError(f"Failed to pull APK: {result.stderr}")

        if not os.path.exists(local_path):
            raise ADBError("APK file not found after pull")

        logger.info("APK extracted to: %s", local_path)
        return local_path

    def backup(self, package: str, output_dir: str = DEFAULT_BACKUP_DIR) -> str:
        os.makedirs(output_dir, exist_ok=True)
        return self.extract(package, output_dir=output_dir)
