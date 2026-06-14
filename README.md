# AndroidBuildBy

Desktop tool for analyzing Android app tech stacks - a LibChecker alternative for your computer.

## Features

- **Device Connection**: Auto-detect Android devices via USB debugging (ADB)
- **App List**: Browse all installed apps with search & filter (user/system)
- **APK Backup**: Extract APK files from device to local storage
- **Tech Stack Analysis**: Detect frameworks, SDKs, and native libraries
  - Cross-platform frameworks: Flutter, React Native, Unity, Xamarin/MAUI, Cordova, Qt
  - 30+ SDK signatures: Firebase, WeChat SDK, Alipay, Umeng, Bugly, etc.
  - Native library analysis with ABI detection
  - SDK version info (Min SDK, Target SDK)
- **Report Export**: JSON, CSV, or plain text
- **Offline Analysis**: Analyze local APK files without device connection

## Requirements

- Python 3.10+
- ADB (Android Debug Bridge) - in PATH
- Android device with USB debugging enabled

## Installation

```bash
# Clone
git clone <repo-url>
cd AndroidBuildBy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main
```

1. Connect your Android device via USB with debugging enabled
2. The app auto-detects your device and lists installed apps
3. Click any app to see basic info
4. Click **Analyze** to extract and scan the APK for tech stack details
5. Click **Backup APK** to save a copy locally
6. Click **Export Report** to save analysis results

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.10+ | Rich ecosystem for APK analysis |
| UI | PySide6 | LGPL license, official Qt binding |
| ADB | subprocess | More reliable than pure-python-adb |
| APK Parsing | androguard + zipfile | Layered: quick scan + deep analysis |
| SDK Detection | JSON rules (data-driven) | Easy to extend without code changes |

## Project Structure

```
src/
├── main.py                    # Entry point
├── core/
│   ├── adb_wrapper.py         # ADB command wrapper
│   ├── device_manager.py      # Device detection & state
│   ├── app_scanner.py         # Scan installed apps
│   ├── apk_extractor.py       # Pull APK from device
│   ├── apk_analyzer.py        # APK parsing & tech stack detection
│   ├── sdk_registry.py        # Load & match SDK detection rules
│   └── report_exporter.py     # Export to JSON/CSV/TXT
├── ui/
│   ├── main_window.py         # Main window layout
│   ├── device_panel.py        # Device info panel
│   ├── app_table.py           # App list with search/filter
│   ├── analysis_view.py       # Tech stack analysis display
│   ├── workers.py             # QThread async workers
│   └── styles.py              # Qt stylesheet
├── models/
│   ├── device.py              # Device data model
│   ├── app_info.py            # App info data model
│   └── analysis_result.py     # Analysis result data model
└── utils/
    ├── elf_parser.py          # ELF header parsing (.so files)
    └── android_versions.py    # API Level ↔ Android version mapping
resources/
└── sdk_rules.json             # SDK/framework detection rules
```

## Adding SDK Detection Rules

Edit `resources/sdk_rules.json` to add new SDK or framework signatures:

```json
{
  "name": "My SDK",
  "category": "category",
  "description": "Description",
  "signatures": {
    "file_paths": ["path/in/apk/"],
    "file_patterns": ["lib/*/libexample.so"],
    "package_names": ["com.example.sdk"],
    "dex_classes": ["Lcom/example/sdk/MainActivity;"]
  }
}
```

## Building Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AndroidBuildBy src/main.py
```

## License

MIT
