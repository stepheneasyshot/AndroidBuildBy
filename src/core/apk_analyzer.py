from __future__ import annotations

import logging
import os
import re
import zipfile
from pathlib import Path

from ..models import AnalysisResult, DetectedSDK, NativeLib, Platform, TechMetadata
from ..utils.android_versions import sdk_to_version
from ..utils.elf_parser import detect_abi_from_path
from .sdk_registry import SDKRegistry

logger = logging.getLogger(__name__)


class QuickScanResult:
    __slots__ = ("file_list", "native_libs", "supported_abis", "has_flutter_assets",
                 "has_react_native", "has_unity", "framework_hints")

    def __init__(self):
        self.file_list: list[str] = []
        self.native_libs: list[NativeLib] = []
        self.supported_abis: list[str] = []
        self.has_flutter_assets = False
        self.has_react_native = False
        self.has_unity = False
        self.framework_hints: list[str] = []


class APKAnalyzer:
    def __init__(self, sdk_registry: SDKRegistry | None = None):
        self.sdk_registry = sdk_registry or SDKRegistry()

    def quick_scan(self, apk_path: str) -> QuickScanResult:
        result = QuickScanResult()

        with zipfile.ZipFile(apk_path, "r") as zf:
            result.file_list = zf.namelist()

            for name in result.file_list:
                lower = name.lower()
                # Native libraries
                if name.startswith("lib/") and name.endswith(".so"):
                    abi = detect_abi_from_path(name) or "unknown"
                    lib_name = os.path.basename(name)
                    size = zf.getinfo(name).file_size
                    result.native_libs.append(NativeLib(name=lib_name, abi=abi, file_size=size))
                    if abi not in result.supported_abis and abi != "unknown":
                        result.supported_abis.append(abi)

                # Framework hints
                if "flutter_assets" in lower:
                    result.has_flutter_assets = True
                    result.framework_hints.append("flutter")
                if "index.android.bundle" in lower or "hermes" in lower:
                    result.has_react_native = True
                    result.framework_hints.append("react_native")
                if "unity" in lower and (name.startswith("assets/bin/Data/") or "libunity.so" in lower):
                    result.has_unity = True
                    result.framework_hints.append("unity")

        result.framework_hints = list(set(result.framework_hints))
        return result

    def deep_analyze(self, apk_path: str) -> AnalysisResult:
        result = AnalysisResult()
        quick = self.quick_scan(apk_path)

        # Set basic metadata
        result.native_libs = quick.native_libs
        result.tech_metadata.supported_abis = quick.supported_abis

        # File-based detection
        file_detected_frameworks = self.sdk_registry.match_frameworks_by_files(quick.file_list)
        file_detected_sdks = self.sdk_registry.match_sdks_by_files(quick.file_list)

        # Androguard deep analysis
        packages: set[str] = set()
        dex_classes: set[str] = set()
        min_sdk = 0
        target_sdk = 0

        try:
            from androguard.core.apk import APK

            apk = APK(apk_path)
            result.app_name = apk.get_app_name()
            result.package_name = apk.get_package()
            min_sdk = apk.get_min_sdk_version() or 0
            target_sdk = apk.get_target_sdk_version() or 0

            # Get permissions
            result.tech_metadata.permissions = apk.get_permissions()

            # Get all dex classes
            for dex in apk.get_all_dex():
                try:
                    from androguard.core.dex import DEX

                    d = DEX(dex)
                    for cls in d.get_classes():
                        cls_name = cls.get_name()
                        dex_classes.add(cls_name)
                        # Extract package from class name like Lcom/example/MyClass;
                        if cls_name.startswith("L") and cls_name.endswith(";"):
                            parts = cls_name[1:-1].split("/")
                            if len(parts) > 1:
                                pkg = ".".join(parts[:-1]).replace("/", ".")
                                packages.add(pkg)
                except Exception:
                    logger.debug("Failed to parse DEX, skipping")

            # Check for Kotlin
            has_kotlin = any("kotlin" in cls for cls in dex_classes)
            has_androidx = any("androidx" in cls for cls in dex_classes)

            # Detect shared user id
            try:
                manifest_xml = apk.get_android_manifest_axml().get_xml()
                if manifest_xml is not None:
                    uid = manifest_xml.get("sharedUserId", "")
                    result.tech_metadata.shared_user_id = uid or ""
            except Exception:
                pass

        except ImportError:
            logger.warning("androguard not available, using quick scan only")
            # Fallback: try to get basic info from manifest
            result.tech_metadata.min_sdk = min_sdk
            result.tech_metadata.target_sdk = target_sdk
        except Exception as e:
            logger.warning("Androguard analysis failed: %s, using quick scan results", e)

        result.tech_metadata.min_sdk = min_sdk
        result.tech_metadata.target_sdk = target_sdk

        # Package/class-based detection
        pkg_detected_frameworks = self.sdk_registry.match_frameworks_by_packages(packages)
        pkg_detected_sdks = self.sdk_registry.match_sdks_by_packages(packages)
        dex_detected = self.sdk_registry.match_by_dex_classes(dex_classes)

        # Merge and deduplicate all detections
        all_frameworks = self._merge_detections(file_detected_frameworks, pkg_detected_frameworks, dex_detected)
        all_sdks = self._merge_detections(file_detected_sdks, pkg_detected_sdks)

        # Determine platform
        result.platform = self._determine_platform(all_frameworks, dex_classes, has_kotlin=True if packages else False)
        result.detected_sdks = all_sdks

        # Check multi-dex
        result.tech_metadata.has_multi_dex = any(
            "classes" in f and f.endswith(".dex") and f != "classes.dex"
            for f in quick.file_list
        )

        return result

    def _determine_platform(
        self,
        detected_frameworks: list[DetectedSDK],
        dex_classes: set[str],
        has_kotlin: bool = False,
    ) -> Platform:
        # Check detected frameworks first
        fw_names = {f.name for f in detected_frameworks}
        name_to_platform = {
            "Flutter": Platform.FLUTTER,
            "React Native": Platform.REACT_NATIVE,
            "Unity": Platform.UNITY,
            "Xamarin/MAUI": Platform.XAMARIN,
            "Cordova": Platform.CORDOVA,
            "Capacitor": Platform.CORDOVA,
            "Qt": Platform.QT,
            "Kotlin/Native": Platform.KOTLIN_NATIVE,
        }
        for name, plat in name_to_platform.items():
            if name in fw_names:
                return plat

        # Heuristic detection from dex classes
        if has_kotlin:
            has_java = any("javax" in cls or "java/lang" in cls for cls in dex_classes)
            if has_java:
                return Platform.KOTLIN
            return Platform.KOTLIN

        has_androidx = any("androidx" in cls for cls in dex_classes)
        has_support = any("android/support" in cls for cls in dex_classes)
        if has_androidx or has_support:
            return Platform.ANDROID_NATIVE

        return Platform.UNKNOWN

    @staticmethod
    def _merge_detections(*detection_lists: list[DetectedSDK]) -> list[DetectedSDK]:
        seen: dict[str, DetectedSDK] = {}
        for dl in detection_lists:
            for d in dl:
                if d.name not in seen:
                    seen[d.name] = d
        return sorted(seen.values(), key=lambda d: d.name)
