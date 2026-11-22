"""
Chaos Game Fractal Generator — Custom Widgets
Enhanced with better gallery and palette preview
"""

from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap

import numpy as np

from config import C, PRESETS, get_cmap


class GalleryWidget(QWidget):
    preset_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_index = -1
        self._buttons: List[QPushButton] = []
        self._build()

    def _build(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(2, 2, 2, 2)
        lo.setSpacing(3)
        hdr = QLabel("Select a preset")
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(f"color:{C['text3']};font-size:9px;padding:2px;")
        lo.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{border:none;background:transparent;}}
            QScrollBar:vertical {{
                background:{C['bg1']};width:5px;border-radius:2px;
            }}
            QScrollBar::handle:vertical {{
                background:{C['bg4']};border-radius:2px;min-height:14px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{height:0;}}
        """)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(4)
        grid.setContentsMargins(2, 2, 2, 2)
        scroll.setWidget(container)
        lo.addWidget(scroll)

        cols = 2
        for i, p in enumerate(PRESETS):
            btn = QPushButton(p["title"])
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            r_val = p.get("r")
            res = p.get("resolution", 1024)
            btn.setToolTip(
                f"Vertices: {p['vertices']}\n"
                f"r: {'random' if r_val is None else r_val}\n"
                f"skip: {p.get('skip', 0)}\n"
                f"resolution: {res}×{res}\n"
                f"palette: {p.get('colormap', '')}"
            )
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._sel(idx))
            grid.addWidget(btn, i // cols, i % cols)
            self._buttons.append(btn)

    def _sel(self, idx):
        self.selected_index = idx
        for i, b in enumerate(self._buttons):
            b.setChecked(i == idx)
        self.preset_selected.emit(idx)

    def clear_selection(self):
        self.selected_index = -1
        for b in self._buttons:
            b.setChecked(False)


class CmapPreviewWidget(QLabel):
    """Enhanced palette preview with better gradient rendering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setMinimumWidth(100)
        self._name = "neon"
        QTimer.singleShot(50, lambda: self.set_cmap(self._name))

    def set_cmap(self, name: str):
        if name.startswith("--"):
            return
        self._name = name
        w = max(self.width(), 160)
        if w < 10:
            return
        
        cmap_obj = get_cmap(name)
        if cmap_obj is None:
            return
            
        # Higher resolution gradient for smoother preview
        gradient = np.linspace(0, 1, min(w * 2, 512)).reshape(1, -1)
        rgba = (cmap_obj(gradient)[:, :, :3] * 255).astype(np.uint8)
        h, _, _ = rgba.shape
        
        # Create image and scale to widget size
        img = QImage(rgba.data, rgba.shape[1], h, 3 * rgba.shape[1],
                     QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(img).scaled(
            self.width(), self.height(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(pix)

    def resizeEvent(self, e):
        self.set_cmap(self._name)
        super().resizeEvent(e)