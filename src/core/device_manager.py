from __future__ import annotations

import logging
from typing import Callable

from ..models import DeviceInfo
from .adb_wrapper import ADBWrapper, ADBError, ADBNotFoundError

logger = logging.getLogger(__name__)


class DeviceManager:
    def __init__(self, adb: ADBWrapper | None = None):
        self.adb = adb or ADBWrapper()
        self._devices: list[DeviceInfo] = []
        self._current_device: DeviceInfo | None = None

    @property
    def devices(self) -> list[DeviceInfo]:
        return self._devices

    @property
    def current_device(self) -> DeviceInfo | None:
        return self._current_device

    @property
    def current_serial(self) -> str:
        return self._current_device.serial if self._current_device else ""

    def refresh_devices(self) -> list[DeviceInfo]:
        try:
            raw_devices = self.adb.get_devices()
            logger.info("ADB device scan: found %d raw device(s)", len(raw_devices))
        except ADBNotFoundError:
            raise
        except ADBError as e:
            logger.error("Failed to refresh devices: %s", e)
            self._devices = []
            return self._devices

        self._devices = []
        for serial, state in raw_devices:
            device = DeviceInfo(serial=serial, is_connected=(state == "device"))
            logger.info("Device %s: state=%s", serial[:16] + "...", state)
            if device.is_connected:
                try:
                    props = self.adb.get_device_properties(device=serial)
                    device.model = props.get("model", "")
                    device.brand = props.get("brand", "")
                    device.android_version = props.get("android_version", "")
                    device.sdk_version = props.get("sdk_version", "")
                    device.device_name = props.get("device", "")
                    logger.info(
                        "  props: brand=%s model=%s android=%s sdk=%s",
                        device.brand, device.model, device.android_version, device.sdk_version,
                    )
                except ADBError:
                    logger.warning("Failed to get properties for device %s", serial)
            self._devices.append(device)

        if self._current_device:
            still_present = any(d.serial == self._current_device.serial for d in self._devices)
            if not still_present:
                logger.info("Previously selected device disconnected")
                self._current_device = None

        connected = [d for d in self._devices if d.is_connected]
        if not self._current_device and connected:
            self._current_device = connected[0]
            logger.info("Auto-selected device: %s", self._current_device.display_name)

        logger.info("Total devices: %d, connected: %d", len(self._devices), len(connected))
        return self._devices

    def select_device(self, serial: str) -> DeviceInfo | None:
        for d in self._devices:
            if d.serial == serial:
                self._current_device = d
                return d
        return None

    def is_adb_available(self) -> bool:
        return self.adb.verify_adb()
