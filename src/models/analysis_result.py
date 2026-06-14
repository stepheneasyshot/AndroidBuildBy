from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Platform(str, Enum):
    ANDROID_NATIVE = "Android Native"
    KOTLIN = "Kotlin"
    FLUTTER = "Flutter"
    REACT_NATIVE = "React Native"
    UNITY = "Unity"
    XAMARIN = "Xamarin/MAUI"
    CORDOVA = "Cordova"
    QT = "Qt"
    KOTLIN_NATIVE = "Kotlin/Native"
    UNKNOWN = "Unknown"


@dataclass
class NativeLib:
    name: str
    abi: str = ""
    file_size: int = 0


@dataclass
class DetectedSDK:
    name: str
    category: str = ""
    description: str = ""


@dataclass
class TechMetadata:
    min_sdk: int = 0
    target_sdk: int = 0
    compile_sdk: int = 0
    supported_abis: list[str] = field(default_factory=list)
    shared_user_id: str = ""
    is_bundle: bool = False
    has_multi_dex: bool = False
    permissions: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    package_name: str = ""
    app_name: str = ""
    platform: Platform = Platform.UNKNOWN
    native_libs: list[NativeLib] = field(default_factory=list)
    detected_sdks: list[DetectedSDK] = field(default_factory=list)
    tech_metadata: TechMetadata = field(default_factory=TechMetadata)
    raw_data: dict[str, Any] = field(default_factory=dict)
