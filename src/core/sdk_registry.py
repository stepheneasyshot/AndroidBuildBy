from __future__ import annotations

import fnmatch
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import DetectedSDK, Platform

logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = Path(__file__).parent.parent.parent / "resources" / "sdk_rules.json"


@dataclass
class FrameworkRule:
    name: str
    category: str
    description: str
    priority: int
    file_paths: list[str]
    file_patterns: list[str]
    package_names: list[str]
    dex_classes: list[str]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FrameworkRule:
        sigs = d.get("signatures", {})
        return cls(
            name=d["name"],
            category=d.get("category", ""),
            description=d.get("description", ""),
            priority=d.get("priority", 99),
            file_paths=sigs.get("file_paths", []),
            file_patterns=sigs.get("file_patterns", []),
            package_names=sigs.get("package_names", []),
            dex_classes=sigs.get("dex_classes", []),
        )


@dataclass
class SDKRule:
    name: str
    category: str
    description: str
    file_paths: list[str]
    file_patterns: list[str]
    package_names: list[str]
    dex_classes: list[str]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SDKRule:
        sigs = d.get("signatures", {})
        return cls(
            name=d["name"],
            category=d.get("category", ""),
            description=d.get("description", ""),
            file_paths=sigs.get("file_paths", []),
            file_patterns=sigs.get("file_patterns", []),
            package_names=sigs.get("package_names", []),
            dex_classes=sigs.get("dex_classes", []),
        )


class SDKRegistry:
    def __init__(self, rules_path: str | Path | None = None):
        self.frameworks: list[FrameworkRule] = []
        self.sdks: list[SDKRule] = []
        self._load_rules(rules_path or DEFAULT_RULES_PATH)

    def _load_rules(self, path: Path):
        if not path.exists():
            logger.warning("SDK rules file not found: %s", path)
            return

        with open(path) as f:
            data = json.load(f)

        for fw in data.get("frameworks", []):
            self.frameworks.append(FrameworkRule.from_dict(fw))

        for sdk in data.get("sdks", []):
            self.sdks.append(SDKRule.from_dict(sdk))

        logger.info("Loaded %d framework rules, %d SDK rules", len(self.frameworks), len(self.sdks))

    # --- Matching methods ---

    def match_frameworks_by_files(self, file_list: list[str]) -> list[DetectedSDK]:
        results = []
        for fw in self.frameworks:
            if self._match_file_signatures(file_list, fw.file_paths, fw.file_patterns):
                results.append(DetectedSDK(name=fw.name, category=fw.category, description=fw.description))
        return results

    def match_sdks_by_files(self, file_list: list[str]) -> list[DetectedSDK]:
        results = []
        for sdk in self.sdks:
            if self._match_file_signatures(file_list, sdk.file_paths, sdk.file_patterns):
                results.append(DetectedSDK(name=sdk.name, category=sdk.category, description=sdk.description))
        return results

    def match_frameworks_by_packages(self, packages: set[str]) -> list[DetectedSDK]:
        results = []
        for fw in self.frameworks:
            if self._match_package_signatures(packages, fw.package_names):
                results.append(DetectedSDK(name=fw.name, category=fw.category, description=fw.description))
        return results

    def match_sdks_by_packages(self, packages: set[str]) -> list[DetectedSDK]:
        results = []
        for sdk in self.sdks:
            if self._match_package_signatures(packages, sdk.package_names):
                results.append(DetectedSDK(name=sdk.name, category=sdk.category, description=sdk.description))
        return results

    def match_by_dex_classes(self, dex_classes: set[str]) -> list[DetectedSDK]:
        results = []
        for fw in self.frameworks:
            for sig_cls in fw.dex_classes:
                if any(sig_cls in cls for cls in dex_classes):
                    results.append(DetectedSDK(name=fw.name, category=fw.category, description=fw.description))
                    break
        for sdk in self.sdks:
            for sig_cls in sdk.dex_classes:
                if any(sig_cls in cls for cls in dex_classes):
                    results.append(DetectedSDK(name=sdk.name, category=sdk.category, description=sdk.description))
                    break
        return results

    # --- Helpers ---

    @staticmethod
    def _match_file_signatures(file_list: list[str], file_paths: list[str], file_patterns: list[str]) -> bool:
        file_set = set(file_list)
        for fp in file_paths:
            if any(fp in f for f in file_set):
                return True
        for pattern in file_patterns:
            matched = fnmatch.filter(file_set, pattern)
            if matched:
                return True
        return False

    @staticmethod
    def _match_package_signatures(packages: set[str], signatures: list[str]) -> bool:
        for sig in signatures:
            if any(pkg.startswith(sig) for pkg in packages):
                return True
        return False
