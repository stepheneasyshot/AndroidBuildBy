# CLAUDE.md

AndroidBuildBy 是一个桌面端 Android 应用技术栈分析工具（类似 LibChecker 的桌面版）。

## 技术栈

- **语言 & 解释器**: Python 3.10+
- **UI 框架**: PySide6 (Qt for Python, LGPL) — 切勿使用 PyQt6
- **ADB**: `subprocess` 直接调用 adb 命令，没有用 pure-python-adb
- **APK 解析**: androguard (深度解析) + zipfile (快速扫描)
- **样式**: QSS 样式表，统一在 `src/ui/styles.py` 定义
- **打包**: PyInstaller（分发用）

## 项目结构 (27 files / ~1900 lines)

```
src/
├── main.py                          # QApplication 入口
├── __main__.py                      # python -m src.main 入口
├── core/
│   ├── adb_wrapper.py               # adb 命令封装 (173行)
│   ├── device_manager.py            # 设备检测、状态管理
│   ├── app_scanner.py               # 扫描已安装应用
│   ├── apk_extractor.py             # 从设备拉取 APK
│   ├── apk_analyzer.py              # APK 分层解析 + 技术栈检测 (202行)
│   ├── sdk_registry.py              # 加载 & 匹配 SDK/框架检测规则
│   └── report_exporter.py           # 导出 JSON/CSV/TXT
├── ui/
│   ├── main_window.py               # 主窗口 (Master-Detail 布局)
│   ├── device_panel.py              # 设备选择 + 状态面板
│   ├── app_table.py                 # 应用列表表格 (搜索/筛选)
│   ├── analysis_view.py             # 技术栈分析结果展示
│   ├── workers.py                   # QThread 异步 Worker (扫描/分析/备份/导出)
│   └── styles.py                    # 全局 QSS 样式 + 颜色常量
├── models/
│   ├── device.py                    # DeviceInfo dataclass
│   ├── app_info.py                  # AppInfo dataclass
│   └── analysis_result.py          # AnalysisResult, Platform, DetectedSDK 等
└── utils/
    ├── android_versions.py          # API Level ↔ Android 版本名映射
    └── elf_parser.py                # ELF header 解析 (.so 文件 ABI 检测)
resources/
└── sdk_rules.json                   # SDK/框架检测规则 (数据驱动, 8框架+32SDK)
```

## 架构要点

### 数据流
1. 用户操作 → `main_window.py` 信号处理
2. `main_window.py` 调用 `core/` 模块执行实际逻辑
3. 耗时操作通过 `ui/workers.py` 中的 QThread 执行，不阻塞 UI
4. Worker 通过 Signal 将结果传回 UI 线程

### APK 分析分层策略
- **Layer 1 (quick_scan)**: zipfile 遍历 APK 文件列表，<1s，检测 .so、assets、框架特征文件
- **Layer 2 (deep_analyze)**: androguard 解析 DEX/Manifest，3-15s，检测包名、类名、权限

### SDK 检测 (数据驱动)
- 规则文件 `resources/sdk_rules.json`，包含 frameworks + sdks 两个分类
- `sdk_registry.py` 加载规则，按 3 层匹配：file_paths/file_patterns → package_names → dex_classes
- 添加新 SDK 只需编辑 JSON，无需改代码

### is_system 判断
- 通过 `adb shell pm list packages -s` 获取系统包集合
- 不解析 `dumpsys package` 的 flags 字段（格式是 `flags=[...]`，不是 hex）

### QThread Worker 模式
```python
worker = SomeWorker(args)
worker.finished.connect(self._on_done)
worker.error.connect(self._on_error)
worker.start()
```
- finished Signal 携带结果数据
- error Signal 携带错误消息字符串
- 长时间运行的 worker 应提供 progress Signal

## 关键约束

- PySide6 信号命名：没有 `currentRowChanged`，用 `currentCellChanged(row, col, prevRow, prevCol)`
- androguard 是可选依赖 —— 如果未安装，analyzer 回退到 zipfile-only 模式
- adb 路径检查用 `shutil.which()`，如果不在 PATH 则在启动时弹窗提示
- 设备连接需要 USB 调试授权，否则设备显示 [unauthorized]
- macOS 运行时会输出 `CFMessagePortSendRequest FAILED` 日志，是无害的系统日志，忽略即可
- UI 最小尺寸 1100x700，左面板 320-500px

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python -m src.main

# 打包
pip install pyinstaller
pyinstaller --onefile --windowed --name AndroidBuildBy src/main.py

# 代码检查
pip install ruff
ruff check src/
```
