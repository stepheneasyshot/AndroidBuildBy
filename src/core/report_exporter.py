from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from ..models import AnalysisResult
from ..utils.android_versions import sdk_to_version


class ReportExporter:
    def to_json(self, result: AnalysisResult, output_path: str):
        data = self._result_to_dict(result)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def to_csv(self, result: AnalysisResult, output_path: str):
        data = self._result_to_flat_rows(result)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["category", "name", "detail"])
            writer.writeheader()
            writer.writerows(data)

    def to_text(self, result: AnalysisResult, output_path: str):
        text = self._result_to_text(result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

    def _result_to_dict(self, r: AnalysisResult) -> dict:
        return {
            "package_name": r.package_name,
            "app_name": r.app_name,
            "platform": r.platform.value,
            "tech_metadata": {
                "min_sdk": r.tech_metadata.min_sdk,
                "min_sdk_version": sdk_to_version(r.tech_metadata.min_sdk) if r.tech_metadata.min_sdk else "",
                "target_sdk": r.tech_metadata.target_sdk,
                "target_sdk_version": sdk_to_version(r.tech_metadata.target_sdk) if r.tech_metadata.target_sdk else "",
                "supported_abis": r.tech_metadata.supported_abis,
                "shared_user_id": r.tech_metadata.shared_user_id,
                "has_multi_dex": r.tech_metadata.has_multi_dex,
                "permissions": r.tech_metadata.permissions,
            },
            "native_libs": [
                {"name": lib.name, "abi": lib.abi, "size": lib.file_size}
                for lib in r.native_libs
            ],
            "detected_sdks": [
                {"name": sdk.name, "category": sdk.category, "description": sdk.description}
                for sdk in r.detected_sdks
            ],
        }

    def _result_to_flat_rows(self, r: AnalysisResult) -> list[dict]:
        rows = []
        meta = r.tech_metadata
        rows.append({"category": "Basic", "name": "Package", "detail": r.package_name})
        rows.append({"category": "Basic", "name": "App Name", "detail": r.app_name})
        rows.append({"category": "Basic", "name": "Platform", "detail": r.platform.value})
        rows.append({"category": "SDK", "name": "Min SDK", "detail": str(meta.min_sdk)})
        rows.append({"category": "SDK", "name": "Target SDK", "detail": str(meta.target_sdk)})
        rows.append({"category": "SDK", "name": "Supported ABIs", "detail": ", ".join(meta.supported_abis)})

        for lib in r.native_libs:
            rows.append({"category": "Native Lib", "name": lib.name, "detail": lib.abi})
        for sdk in r.detected_sdks:
            rows.append({"category": "SDK", "name": sdk.name, "detail": sdk.category})
        return rows

    def _result_to_text(self, r: AnalysisResult) -> str:
        lines = []
        sep = "=" * 50
        sub = "-" * 50

        lines.append(sep)
        lines.append(f"App Name: {r.app_name}")
        lines.append(f"Package: {r.package_name}")
        lines.append(sub)
        lines.append(f"Platform: {r.platform.value}")

        meta = r.tech_metadata
        if meta.min_sdk:
            lines.append(f"Min SDK: {meta.min_sdk} ({sdk_to_version(meta.min_sdk)})")
        if meta.target_sdk:
            lines.append(f"Target SDK: {meta.target_sdk} ({sdk_to_version(meta.target_sdk)})")
        lines.append(sub)

        if r.native_libs:
            lines.append(f"Native Libraries ({len(r.native_libs)}):")
            for lib in r.native_libs:
                lines.append(f"  - {lib.name}  [{lib.abi}]")
            if meta.supported_abis:
                lines.append(f"Supported ABIs: {', '.join(meta.supported_abis)}")
            lines.append(sub)

        if r.detected_sdks:
            lines.append("Detected SDKs:")
            for sdk in r.detected_sdks:
                cat = f" ({sdk.category})" if sdk.category else ""
                lines.append(f"  - {sdk.name}{cat}")
            lines.append(sub)

        if meta.permissions:
            lines.append(f"Permissions ({len(meta.permissions)}):")
            for perm in meta.permissions:
                lines.append(f"  - {perm}")

        lines.append(sep)
        return "\n".join(lines)
