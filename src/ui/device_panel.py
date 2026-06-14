from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..models import DeviceInfo
from .styles import COLOR_SUCCESS, COLOR_ERROR


class DevicePanel(QWidget):
    device_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)

        group = QGroupBox("Device")
        group_layout = QVBoxLayout(group)

        # Device selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        selector_layout.addWidget(self.device_combo, stretch=1)
        group_layout.addLayout(selector_layout)

        # Device detail info
        form = QFormLayout()
        form.setSpacing(4)

        self.label_status = QLabel("No device")
        self.label_serial = QLabel("-")
        self.label_brand = QLabel("-")
        self.label_model = QLabel("-")
        self.label_android = QLabel("-")
        self.label_sdk = QLabel("-")

        form.addRow("Status:", self.label_status)
        form.addRow("Serial:", self.label_serial)
        form.addRow("Brand:", self.label_brand)
        form.addRow("Model:", self.label_model)
        form.addRow("Android:", self.label_android)
        form.addRow("SDK:", self.label_sdk)

        group_layout.addLayout(form)
        layout.addWidget(group)

        self.device_combo.currentIndexChanged.connect(self._on_combo_changed)

    def update_devices(self, devices: list[DeviceInfo], current: DeviceInfo | None = None):
        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        for d in devices:
            label = f"{d.display_name} ({d.serial[:16]}...)" if len(d.serial) > 16 else f"{d.display_name} ({d.serial})"
            if not d.is_connected:
                label += " [unauthorized]"
            self.device_combo.addItem(label, d.serial)

        if current:
            idx = self.device_combo.findData(current.serial)
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)

        self.device_combo.blockSignals(False)
        self._update_info(current)

    def _on_combo_changed(self, index: int):
        serial = self.device_combo.itemData(index)
        if serial:
            self.device_selected.emit(serial)

    def _update_info(self, device: DeviceInfo | None):
        if not device:
            self.label_status.setText("No device")
            self.label_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
            for lbl in (self.label_serial, self.label_brand, self.label_model, self.label_android, self.label_sdk):
                lbl.setText("-")
            return

        if device.is_connected:
            self.label_status.setText("Connected")
            self.label_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
        else:
            self.label_status.setText("Unauthorized")
            self.label_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")

        self.label_serial.setText(device.serial)
        self.label_brand.setText(device.brand or "-")
        self.label_model.setText(device.model or "-")
        self.label_android.setText(device.android_version or "-")
        self.label_sdk.setText(device.sdk_version or "-")
