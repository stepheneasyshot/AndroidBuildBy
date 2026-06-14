from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    return_code: int

    @property
    def output(self) -> str:
        return self.stdout.strip()


class ADBError(Exception):
    pass


class ADBNotFoundError(ADBError):
    pass


class DeviceNotFoundError(ADBError):
    pass


class ADBWrapper:
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self._verified: bool | None = None

    def verify_adb(self) -> bool:
        if self._verified is not None:
            return self._verified
        found = shutil.which(self.adb_path) is not None
        if not found:
            # Try common locations
            logger.warning("adb not found in PATH: %s", self.adb_path)
        self._verified = found
        return found

    def _run(self, args: list[str], timeout: int = 30, device: str = "") -> CommandResult:
        if not self.verify_adb():
            raise ADBNotFoundError("adb not found. Install Android Platform Tools and add to PATH.")

        cmd = [self.adb_path]
        if device:
            cmd.extend(["-s", device])
        cmd.extend(args)

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return CommandResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                return_code=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            raise ADBError(f"ADB command timed out: {' '.join(args)}")
        except FileNotFoundError:
            raise ADBNotFoundError(f"adb executable not found: {self.adb_path}")

    def get_devices(self) -> list[tuple[str, str]]:
        result = self._run(["devices"])
        if not result.success:
            raise ADBError(f"Failed to list devices: {result.stderr}")

        devices = []
        for line in result.output.split("\n")[1:]:
            line = line.strip()
            if not line or line.startswith("*"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                devices.append((parts[0], parts[1]))
        return devices

    def get_device_properties(self, device: str = "") -> dict[str, str]:
        props = {}
        for prop_name, prop_key in [
            ("model", "ro.product.model"),
            ("brand", "ro.product.brand"),
            ("device", "ro.product.device"),
            ("android_version", "ro.build.version.release"),
            ("sdk_version", "ro.build.version.sdk"),
            ("manufacturer", "ro.product.manufacturer"),
        ]:
            result = self._run(["shell", "getprop", prop_key], device=device)
            if result.success:
                props[prop_name] = result.output
        return props

    def get_installed_packages(self, device: str = "", user_only: bool = True) -> list[str]:
        args = ["shell", "pm", "list", "packages"]
        if user_only:
            args.append("-3")
        result = self._run(args, device=device, timeout=60)
        if not result.success:
            raise ADBError(f"Failed to list packages: {result.stderr}")

        packages = []
        for line in result.output.split("\n"):
            line = line.strip()
            if line.startswith("package:"):
                packages.append(line[8:])
        return packages

    def get_system_packages(self, device: str = "") -> set[str]:
        result = self._run(["shell", "pm", "list", "packages", "-s"], device=device, timeout=60)
        if not result.success:
            return set()
        packages = set()
        for line in result.output.split("\n"):
            line = line.strip()
            if line.startswith("package:"):
                packages.add(line[8:])
        return packages

    def get_package_info(self, package: str, device: str = "") -> dict[str, str]:
        result = self._run(["shell", "dumpsys", "package", package], device=device, timeout=30)
        if not result.success:
            return {}

        info: dict[str, str] = {}
        for line in result.output.split("\n"):
            line = line.strip()
            if line.startswith("versionName="):
                info["version_name"] = line.split("=", 1)[1]
            elif line.startswith("versionCode="):
                val = line.split("=", 1)[1]
                info["version_code"] = val.split(" ", 1)[0]
            elif line.startswith("targetSdk="):
                info["target_sdk"] = line.split("=", 1)[1].split(" ", 1)[0]
            elif "codePath=" in line:
                info["apk_path"] = line.split("codePath=", 1)[1].strip()
            elif line.startswith("firstInstallTime="):
                info["install_time"] = line.split("=", 1)[1]
        return info

    def get_package_path(self, package: str, device: str = "") -> str:
        result = self._run(["shell", "pm", "path", package], device=device)
        if not result.success:
            return ""
        for line in result.output.split("\n"):
            line = line.strip()
            if line.startswith("package:"):
                return line[8:]
        return ""

    def pull_file(self, remote: str, local: str, device: str = "") -> CommandResult:
        return self._run(["pull", remote, local], device=device, timeout=300)

    def get_app_label(self, package: str, device: str = "") -> str:
        result = self._run(
            ["shell", "dumpsys", "package", package, "|", "grep", "-A1", "ApplicationInfo"],
            device=device,
        )
        if result.output:
            return result.output.strip()
        return package

    def shell(self, cmd: str, device: str = "", timeout: int = 30) -> str:
        result = self._run(["shell", cmd], device=device, timeout=timeout)
        return result.output
