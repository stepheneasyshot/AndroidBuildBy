from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppInfo:
    package_name: str
    app_name: str = ""
    version_name: str = ""
    version_code: int = 0
    is_system: bool = False
    install_time: str = ""
    target_sdk: int = 0
    min_sdk: int = 0
    apk_path: str = ""
    icon_path: str = ""

    @property
    def display_name(self) -> str:
        return self.app_name or self.package_name

    @property
    def version_display(self) -> str:
        if self.version_name and self.version_code:
            return f"{self.version_name} ({self.version_code})"
        return self.version_name or str(self.version_code)
