"""
Chaos Game Fractal Generator — QSS Theme Stylesheet
"""

from config import C

STYLESHEET = f"""
    QMainWindow, QWidget {{
        background: {C['bg1']};
        color: {C['text']};
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 11px;
    }}
    QGroupBox {{
        border: 1px solid {C['border']};
        border-radius: 7px;
        margin-top: 13px;
        padding: 10px 8px 6px 8px;
        font-weight: bold;
        font-size: 10px;
        color: {C['text2']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    QLabel {{ color: {C['text2']}; font-size: 10px; }}
    QSpinBox, QDoubleSpinBox {{
        background: {C['bg2']};
        border: 1px solid {C['border']};
        border-radius: 5px;
        padding: 3px 6px;
        color: {C['text']};
        min-height: 22px;
        selection-background-color: {C['accent2']};
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {C['accent']};
    }}
    QComboBox {{
        background: {C['bg2']};
        border: 1px solid {C['border']};
        border-radius: 5px;
        padding: 3px 6px;
        color: {C['text']};
        min-height: 22px;
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {C['text3']};
        margin-right: 5px;
    }}
    QComboBox QAbstractItemView {{
        background: {C['bg2']};
        border: 1px solid {C['border']};
        color: {C['text']};
        selection-background-color: {C['accent2']};
        outline: none;
    }}
    QCheckBox {{
        color: {C['text2']};
        font-size: 10px;
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px; height: 14px;
        border-radius: 3px;
        border: 1px solid {C['border']};
        background: {C['bg2']};
    }}
    QCheckBox::indicator:checked {{
        background: {C['accent2']};
        border-color: {C['accent']};
    }}
    QCheckBox::indicator:hover {{ border-color: {C['accent']}; }}
    QSlider::groove:horizontal {{
        border: 1px solid {C['border']};
        height: 4px;
        background: {C['bg2']};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {C['accent']};
        border: none;
        width: 13px; height: 13px;
        margin: -5px 0;
        border-radius: 6px;
    }}
    QSlider::sub-page:horizontal {{
        background: {C['accent2']};
        border-radius: 2px;
    }}
    QPushButton {{
        background: {C['bg2']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        padding: 6px 12px;
        color: {C['text']};
        font-size: 11px;
        font-weight: bold;
        min-height: 24px;
    }}
    QPushButton:hover {{
        background: {C['bg3']};
        border-color: {C['accent']};
    }}
    QPushButton:pressed {{ background: {C['bg4']}; }}
    QPushButton:disabled {{
        background: {C['bg0']};
        color: {C['text3']};
        border-color: {C['border']};
    }}
    QPushButton:checked {{
        background: {C['accent_dim']};
        border-color: {C['accent']};
        color: {C['accent']};
    }}
    QProgressBar {{
        border: 1px solid {C['border']};
        border-radius: 4px;
        text-align: center;
        background: {C['bg2']};
        color: {C['text']};
        font-size: 9px;
        min-height: 14px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {C['accent2']}, stop:1 {C['accent']}
        );
        border-radius: 3px;
    }}
    QStatusBar {{
        background: {C['bg0']};
        color: {C['text3']};
        font-size: 10px;
        border-top: 1px solid {C['border']};
    }}
    QTabWidget::pane {{
        border: 1px solid {C['border']};
        border-radius: 6px;
        background: {C['bg1']};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {C['bg2']};
        color: {C['text3']};
        border: 1px solid {C['border']};
        padding: 5px 9px;
        margin-right: 1px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-size: 10px;
        font-weight: bold;
    }}
    QTabBar::tab:selected {{
        background: {C['bg1']};
        color: {C['accent']};
        border-bottom-color: {C['bg1']};
    }}
    QTabBar::tab:hover {{ color: {C['text']}; }}
"""

GENERATE_BUTTON_STYLE = f"""
    QPushButton {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {C['accent2']}, stop:1 {C['accent']}
        );
        color: #fff;
        border: none;
        font-size: 13px;
        padding: 10px;
        border-radius: 8px;
    }}
    QPushButton:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 #0f766e, stop:1 #0d9488
        );
    }}
    QPushButton:pressed {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 #115e59, stop:1 #0f766e
        );
    }}
    QPushButton:disabled {{
        background: {C['bg0']};
        color: {C['text3']};
    }}
"""

CLEAR_BUTTON_STYLE = f"""
    QPushButton {{
        background: {C['bg0']};
        border-color: #3a1a2e;
        color: {C['rose']};
    }}
    QPushButton:hover {{
        background: #1a0e14;
        border-color: #5a2a4e;
    }}
"""

SCROLL_STYLE = f"""
    QScrollArea {{border:none;background:transparent;}}
    QScrollBar:vertical {{
        background:{C['bg1']};width:4px;border-radius:2px;
    }}
    QScrollBar::handle:vertical {{
        background:{C['bg4']};border-radius:2px;min-height:12px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{height:0;}}
"""