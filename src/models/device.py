from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeviceInfo:
    serial: str
    model: str = ""
    brand: str = ""
    android_version: str = ""
    sdk_version: str = ""
    device_name: str = ""
    is_connected: bool = True

    @property
    def display_name(self) -> str:
        parts = [self.brand, self.model] if self.brand and self.model else [self.device_name or self.serial]
        return " ".join(parts).strip()
