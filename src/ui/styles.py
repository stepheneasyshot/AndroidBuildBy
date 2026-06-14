APP_NAME = "AndroidBuildBy"
APP_VERSION = "1.0.0"

MAIN_WINDOW_MIN_WIDTH = 1100
MAIN_WINDOW_MIN_HEIGHT = 700
LEFT_PANEL_WIDTH = 320

COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_DARK = "#1976D2"
COLOR_ACCENT = "#FF9800"
COLOR_BG = "#FAFAFA"
COLOR_SURFACE = "#FFFFFF"
COLOR_TEXT = "#212121"
COLOR_TEXT_SECONDARY = "#757575"
COLOR_BORDER = "#E0E0E0"
COLOR_SUCCESS = "#4CAF50"
COLOR_WARNING = "#FF9800"
COLOR_ERROR = "#F44336"

MAIN_STYLESHEET = f"""
    QWidget {{
        color: {COLOR_TEXT};
        font-size: 13px;
    }}
    QMainWindow {{
        background-color: {COLOR_BG};
    }}
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 16px;
        color: {COLOR_TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {COLOR_TEXT};
    }}
    QLabel {{
        color: {COLOR_TEXT};
    }}
    QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        min-height: 28px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_PRIMARY_DARK};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_PRIMARY_DARK};
    }}
    QPushButton:disabled {{
        background-color: #BDBDBD;
        color: #EEEEEE;
    }}
    QPushButton[class="secondary"] {{
        background-color: transparent;
        color: {COLOR_PRIMARY};
        border: 1px solid {COLOR_PRIMARY};
    }}
    QPushButton[class="secondary"]:hover {{
        background-color: rgba(33, 150, 243, 0.08);
    }}
    QLineEdit {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 6px 10px;
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border-color: {COLOR_PRIMARY};
    }}
    QComboBox {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        gridline-color: {COLOR_BORDER};
        selection-background-color: rgba(33, 150, 243, 0.12);
        selection-color: {COLOR_TEXT};
        alternate-background-color: #F9F9F9;
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        color: {COLOR_TEXT};
    }}
    QHeaderView::section {{
        background-color: #F5F5F5;
        border: none;
        border-bottom: 2px solid {COLOR_BORDER};
        padding: 6px 8px;
        font-weight: bold;
        font-size: 12px;
        color: {COLOR_TEXT_SECONDARY};
    }}
    QCheckBox {{
        spacing: 6px;
        font-size: 13px;
        color: {COLOR_TEXT};
    }}
    QLabel[class="title"] {{
        font-size: 18px;
        font-weight: bold;
        color: {COLOR_TEXT};
    }}
    QLabel[class="subtitle"] {{
        font-size: 13px;
        color: {COLOR_TEXT_SECONDARY};
    }}
    QLabel[class="value"] {{
        font-size: 14px;
        color: {COLOR_TEXT};
    }}
    QProgressBar {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        text-align: center;
        background-color: #F5F5F5;
        color: {COLOR_TEXT};
        height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {COLOR_PRIMARY};
        border-radius: 3px;
    }}
    QStatusBar {{
        background-color: #F5F5F5;
        border-top: 1px solid {COLOR_BORDER};
        font-size: 12px;
        color: {COLOR_TEXT_SECONDARY};
    }}
    QSplitter::handle {{
        background-color: {COLOR_BORDER};
        width: 1px;
    }}
"""
