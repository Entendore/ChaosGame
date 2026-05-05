"""
Chaos Game Fractal Generator — PySide6 GUI Application
High-performance bitmap rendering with refined dark theme.
"""

import sys
import os
import time
import math
import random
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QComboBox, QSlider, QGroupBox, QScrollArea,
    QFileDialog, QProgressBar, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QImage, QPixmap, QShortcut, QKeySequence

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.pyplot as plt
import matplotlib


# ============================================================
# Safe colormap accessor (handles deprecation in mpl ≥ 3.7)
# ============================================================
def get_cmap(name: str):
    try:
        return matplotlib.colormaps[name]
    except (AttributeError, KeyError):
        import matplotlib.cm as cm
        return cm.get_cmap(name)


# ============================================================
# Color Palette — "Midnight Observatory"
# ============================================================
C = {
    "bg0":       "#080c14",
    "bg1":       "#0d1220",
    "bg2":       "#131a2b",
    "bg3":       "#1a2438",
    "bg4":       "#222e44",
    "border":    "#1c2a3e",
    "accent":    "#14b8a6",
    "accent2":   "#0d9488",
    "accent_dim":"#0a6b63",
    "text":      "#e2e8f0",
    "text2":     "#94a3b8",
    "text3":     "#475569",
    "rose":      "#f43f5e",
    "canvas_bg": "#080c14",
}

BG_RGB = (8, 12, 20)
DISPLAY_RES = 2048
EXPORT_RES   = 4096
ANIM_RES     = 1536
SCATTER_THRESHOLD = 30_000


# ============================================================
# Presets with curated palettes
# ============================================================
PRESETS: List[Dict[str, Any]] = [
    {"vertices": 3,  "r": 0.5,   "title": "Sierpinski Triangle",
     "colormap": "turbo",           "point_size": 10},
    {"vertices": 3,  "r": None,   "title": "Triangle · Random r",
     "colormap": "inferno",         "point_size": 10},
    {"vertices": 4,  "r": 0.5,   "no_repeat": True,
     "title": "Square No-Repeat",   "colormap": "Set2",        "point_size": 10},
    {"vertices": 4,  "r": 0.5,   "skip": 1,
     "title": "Square Maze",        "colormap": "magma",       "point_size": 8},
    {"vertices": 5,  "r": 0.618, "title": "Golden Pentagon",
     "colormap": "YlOrBr",          "point_size": 10},
    {"vertices": 5,  "r": 0.618, "skip": 1,
     "title": "Pentagram Void",     "colormap": "twilight",    "point_size": 10},
    {"vertices": 6,  "r": 0.5,   "title": "Hexagonal Snowflake",
     "colormap": "cool",            "point_size": 8},
    {"vertices": 6,  "r": 1/3,   "title": "Hexagon r = ⅓",
     "colormap": "Paired",          "point_size": 10},
    {"vertices": 6,  "r": 0.5,   "skip": 2,
     "title": "Star of David",      "colormap": "hot",         "point_size": 15},
    {"vertices": 7,  "r": 0.5,   "random_vertices": True,
     "title": "Chaotic Heptagon",   "colormap": "nipy_spectral","point_size": 10},
    {"vertices": 8,  "r": 0.5,   "title": "Octagonal Vortex",
     "colormap": "cubehelix",       "point_size": 6},
    {"vertices": 8,  "r": 0.618, "title": "Octagon Golden",
     "colormap": "cividis",         "point_size": 8},
    {"vertices": 9,  "r": 0.45,  "skip": 1,
     "title": "Nonagonal Nebula",   "colormap": "Spectral",    "point_size": 6},
    {"vertices": 10, "r": 0.7,   "title": "Decagon Chaos",
     "colormap": "plasma",          "point_size": 6},
    {"vertices": 10, "r": 0.5,   "title": "Decagonal Bloom",
     "colormap": "PuBu",            "point_size": 6},
    {"vertices": 12, "r": 0.5,   "title": "Dodecagonal Cosmos",
     "colormap": "rainbow",         "point_size": 4},
]

COLORMAPS = [
    "turbo", "viridis", "plasma", "inferno", "magma", "cividis",
    "hot", "cool", "warm", "twilight", "twilight_shifted", "cubehelix",
    "nipy_spectral", "rainbow", "gist_earth", "gist_stern",
    "tab10", "tab20", "Set1", "Set2", "Set3", "Paired",
    "Dark2", "Accent", "Pastel1", "Spectral", "RdYlBu", "RdPu",
    "BuGn", "PuBu", "YlOrBr", "YlOrRd", "spring", "summer",
    "autumn", "winter", "bone", "pink", "gray",
]


# ============================================================
# Bitmap Renderer
# ============================================================
class BitmapRenderer:
    """Renders chaos-game points to numpy arrays via bincount."""

    @staticmethod
    def _map(xs, ys, w, h, xlim, ylim):
        px = ((xs - xlim[0]) / (xlim[1] - xlim[0]) * (w - 1)).astype(np.int32)
        py = (1.0 - (ys - ylim[0]) / (ylim[1] - ylim[0]) * (h - 1)).astype(np.int32)
        mask = (px >= 0) & (px < w) & (py >= 0) & (py < h)
        return px[mask], py[mask]

    @staticmethod
    def _build_lut(cmap_name, c_max):
        cmap_obj = get_cmap(cmap_name)
        return (cmap_obj(np.linspace(0, 1, c_max + 1))[:, :3] * 255).astype(np.uint8)

    @staticmethod
    def render(
        xs, ys, colors,
        width=DISPLAY_RES, height=DISPLAY_RES,
        xlim=(-1.3, 1.3), ylim=(-1.3, 1.3),
        cmap_name="viridis", bg=BG_RGB,
        glow=True, glow_radius=1, glow_intensity=0.18,
    ) -> np.ndarray:
        px, py = BitmapRenderer._map(xs, ys, width, height, xlim, ylim)
        if len(px) == 0:
            return np.full((height, width, 3), bg, dtype=np.uint8)

        c = colors[:len(px)]
        c_max = max(int(c.max()), 1)
        lut = BitmapRenderer._build_lut(cmap_name, c_max).astype(np.float32)
        pc = lut[c]

        flat = py.astype(np.int64) * width + px.astype(np.int64)
        n_pix = width * height

        img = np.zeros((height, width, 3), dtype=np.float32)
        for ch in range(3):
            img[:, :, ch] = np.bincount(
                flat, weights=pc[:, ch], minlength=n_pix
            )[:n_pix].reshape(height, width)

        weight = np.bincount(flat, minlength=n_pix)[:n_pix].reshape(height, width)
        nz = weight > 0
        img[nz] /= weight[nz, np.newaxis]

        result = np.full((height, width, 3), bg, dtype=np.uint8)
        result[nz] = np.clip(img[nz], 0, 255).astype(np.uint8)

        if glow:
            result = BitmapRenderer._glow(result, glow_radius, glow_intensity, bg)
        return result

    @staticmethod
    def render_direct(
        xs, ys, colors, width, height, xlim, ylim, cmap_name, bg=BG_RGB,
    ) -> np.ndarray:
        px, py = BitmapRenderer._map(xs, ys, width, height, xlim, ylim)
        img = np.full((height, width, 3), bg, dtype=np.uint8)
        if len(px) == 0:
            return img
        c = colors[:len(px)]
        c_max = max(int(c.max()), 1)
        lut = BitmapRenderer._build_lut(cmap_name, c_max)
        img[py, px] = lut[c]
        return img

    @staticmethod
    def _glow(img, radius, intensity, bg):
        h, w = img.shape[:2]
        src = img.astype(np.float32)
        k = 2 * radius + 1
        # horizontal pass
        pad = np.pad(src, ((0, 0), (radius, radius), (0, 0)), mode="edge")
        tmp = np.zeros_like(pad)
        for dx in range(k):
            tmp += pad[:, radius + dx: w + radius + dx, :]
        tmp /= k
        tmp = tmp[:, radius: w + radius, :]
        # vertical pass
        pad2 = np.pad(tmp, ((radius, radius), (0, 0), (0, 0)), mode="edge")
        blurred = np.zeros_like(pad2)
        for dy in range(k):
            blurred += pad2[radius + dy: h + radius + dy, :, :]
        blurred /= k
        glow_img = blurred[radius: h + radius, :, :]

        bg_f = np.array(bg, dtype=np.float32)
        is_bg = np.all(src == bg_f, axis=2)
        out = src * (1 - intensity) + glow_img * intensity
        out[is_bg] = bg_f
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def compute_bounds(xs, ys, margin=0.08):
        x0, x1 = float(xs.min()), float(xs.max())
        y0, y1 = float(ys.min()), float(ys.max())
        rng = max(x1 - x0, y1 - y0, 0.01) * (1 + margin)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half = rng / 2
        return (cx - half, cx + half), (cy - half, cy + half)

    @staticmethod
    def precompute_pixels(xs, ys, w, h, xlim, ylim):
        """Return filtered pixel coords and original indices for slicing."""
        px = ((xs - xlim[0]) / (xlim[1] - xlim[0]) * (w - 1)).astype(np.int32)
        py = (1.0 - (ys - ylim[0]) / (ylim[1] - ylim[0]) * (h - 1)).astype(np.int32)
        mask = (px >= 0) & (px < w) & (py >= 0) & (py < h)
        return px, py, mask


# ============================================================
# Polygon & Chaos Game
# ============================================================
class PolygonGenerator:
    @staticmethod
    def regular(n, radius=1.0, start_angle=math.pi / 2):
        return [
            (radius * math.cos(start_angle + 2 * math.pi * k / n),
             radius * math.sin(start_angle + 2 * math.pi * k / n))
            for k in range(n)
        ]

    @staticmethod
    def random_polygon(n, radius=1.0, seed=None):
        if seed is not None:
            np.random.seed(seed)
        angles = np.sort(np.random.rand(n) * 2 * math.pi)
        return [(math.cos(t) * radius, math.sin(t) * radius) for t in angles]


class ChaosGame:
    def __init__(self, vertices, r=0.5, skip=0, random_vertices=False,
                 no_repeat=False, burn_in=50, iterations=200_000, seed=None):
        self.vertices = vertices
        self.r = r
        self.skip = skip
        self.random_vertices = random_vertices
        self.no_repeat = no_repeat
        self.burn_in = burn_in
        self.iterations = iterations
        self.total_points = iterations + burn_in
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.verts = (
            PolygonGenerator.random_polygon(vertices, seed=seed)
            if random_vertices else PolygonGenerator.regular(vertices)
        )
        self.vx = np.array([v[0] for v in self.verts], dtype=np.float64)
        self.vy = np.array([v[1] for v in self.verts], dtype=np.float64)

        self._skip_tables = None
        if skip > 0:
            self._build_skip_tables()

    def _build_skip_tables(self):
        tables, counts = [], []
        nv = self.vertices
        for i in range(nv):
            v = [j for j in range(nv)
                 if min(abs(i - j), nv - abs(i - j)) > self.skip]
            if not v:
                v = list(range(nv))
            tables.append(np.array(v, dtype=np.int32))
            counts.append(len(v))
        self._skip_tables = (tables, counts)

    def _standard(self):
        nv = self.vertices
        r = self.r
        bi = self.burn_in
        it = self.iterations
        vx, vy = self.vx, self.vy
        nr = self.no_repeat
        xs = np.empty(it, np.float32)
        ys = np.empty(it, np.float32)
        co = np.empty(it, np.int32)
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        prev = -1
        j = 0
        for i in range(bi + it):
            idx = int(random.random() * nv)
            if nr and idx == prev:
                idx = int(random.random() * nv)
                if idx == prev:
                    idx = (prev + 1) % nv
            x += r * (vx[idx] - x)
            y += r * (vy[idx] - y)
            prev = idx
            if i >= bi:
                xs[j] = x
                ys[j] = y
                co[j] = idx
                j += 1
        return xs, ys, co

    def _random_r(self):
        nv = self.vertices
        bi = self.burn_in
        it = self.iterations
        vx, vy = self.vx, self.vy
        xs = np.empty(it, np.float32)
        ys = np.empty(it, np.float32)
        co = np.empty(it, np.int32)
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        j = 0
        for i in range(bi + it):
            idx = int(random.random() * nv)
            rs = 0.3 + 0.4 * random.random()
            x += rs * (vx[idx] - x)
            y += rs * (vy[idx] - y)
            if i >= bi:
                xs[j] = x
                ys[j] = y
                co[j] = idx
                j += 1
        return xs, ys, co

    def _skip(self):
        nv = self.vertices
        r = self.r
        bi = self.burn_in
        it = self.iterations
        vx, vy = self.vx, self.vy
        tables, counts = self._skip_tables
        xs = np.empty(it, np.float32)
        ys = np.empty(it, np.float32)
        co = np.empty(it, np.int32)
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        prev = 0
        j = 0
        for i in range(bi + it):
            t = tables[prev]
            c = counts[prev]
            idx = int(t[int(random.random() * c)])
            x += r * (vx[idx] - x)
            y += r * (vy[idx] - y)
            prev = idx
            if i >= bi:
                xs[j] = x
                ys[j] = y
                co[j] = idx
                j += 1
        return xs, ys, co

    def generate(self):
        if self.r is None:
            return self._random_r()
        if self.skip > 0:
            return self._skip()
        return self._standard()


# ============================================================
# Background worker
# ============================================================
class GenerationWorker(QThread):
    finished = Signal(np.ndarray, np.ndarray, np.ndarray, float, list)
    error = Signal(str)

    def __init__(self, cfg, iterations, seed=None):
        super().__init__()
        self.cfg = cfg
        self.iterations = iterations
        self.seed = seed

    def run(self):
        try:
            t0 = time.perf_counter()
            g = ChaosGame(
                vertices=self.cfg["vertices"],
                r=self.cfg.get("r", 0.5),
                skip=self.cfg.get("skip", 0),
                random_vertices=self.cfg.get("random_vertices", False),
                no_repeat=self.cfg.get("no_repeat", False),
                burn_in=50,
                iterations=self.iterations,
                seed=self.seed,
            )
            xs, ys, colors = g.generate()
            elapsed = time.perf_counter() - t0
            self.finished.emit(xs, ys, colors, elapsed, g.verts)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
# Matplotlib canvas
# ============================================================
class FractalCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi,
                          facecolor=C["canvas_bg"])
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._extent = [-1.5, 1.5, -1.5, 1.5]
        self._img_artist = None
        self._setup()

    def _setup(self):
        ax = self.ax
        ax.set_facecolor(C["canvas_bg"])
        ax.set_xlim(self._extent[0], self._extent[1])
        ax.set_ylim(self._extent[2], self._extent[3])
        ax.set_aspect("equal")
        ax.axis("off")
        self.fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01)

    def set_extent(self, xlim, ylim):
        self._extent = [xlim[0], xlim[1], ylim[0], ylim[1]]

    def clear_plot(self):
        self._extent = [-1.5, 1.5, -1.5, 1.5]
        self.ax.clear()
        self._setup()
        self._img_artist = None
        self.draw_idle()

    def show_bitmap(self, bitmap, title=""):
        self.ax.clear()
        self._setup()
        self._img_artist = self.ax.imshow(
            bitmap, aspect="equal", interpolation="bilinear",
            extent=self._extent, origin="upper",
        )
        if title:
            self.ax.set_title(title, fontsize=11, color=C["text"],
                              pad=6, fontweight="bold", fontfamily="monospace")
        self.draw_idle()

    def update_bitmap(self, bitmap, title=""):
        if self._img_artist is not None:
            self._img_artist.set_data(bitmap)
            if title:
                self.ax.set_title(title, fontsize=11, color=C["text"],
                                  pad=6, fontweight="bold", fontfamily="monospace")
            self.draw_idle()

    def plot_scatter(self, xs, ys, colors, cmap_name="viridis",
                     point_size=0.1, title=""):
        self.ax.clear()
        self._setup()
        self._img_artist = None
        vmin, vmax = int(colors.min()), int(colors.max())
        if vmin == vmax:
            vmax = vmin + 1
        self.ax.scatter(xs, ys, c=colors, cmap=cmap_name, s=point_size,
                        marker=".", alpha=0.9, linewidths=0,
                        vmin=vmin, vmax=vmax, rasterized=True)
        if title:
            self.ax.set_title(title, fontsize=11, color=C["text"],
                              pad=6, fontweight="bold", fontfamily="monospace")
        self.draw_idle()

    def plot_vertices(self, verts):
        vx = [v[0] for v in verts]
        vy = [v[1] for v in verts]
        self.ax.plot(vx + [vx[0]], vy + [vy[0]], "o-",
                     color=C["accent"], markersize=6, linewidth=1.2,
                     alpha=0.8, zorder=10)
        for i, (x, y) in enumerate(verts):
            self.ax.annotate(str(i), (x, y), textcoords="offset points",
                             xytext=(5, 5), fontsize=8, color=C["accent"],
                             fontweight="bold", zorder=11)
        self.draw_idle()


# ============================================================
# Gallery widget
# ============================================================
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
            btn.setToolTip(
                f"Vertices: {p['vertices']}\n"
                f"r: {'random' if r_val is None else r_val}\n"
                f"skip: {p.get('skip', 0)}\n"
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


# ============================================================
# Colormap preview widget
# ============================================================
class CmapPreviewWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setMinimumWidth(100)
        self._name = "viridis"
        self._pix = None
        QTimer.singleShot(50, lambda: self.set_cmap(self._name))

    def set_cmap(self, name: str):
        self._name = name
        w = max(self.width(), 160)
        if w < 10:
            self._pix = None
            return
        gradient = np.linspace(0, 1, w).reshape(1, -1)
        rgba = (get_cmap(name)(gradient)[:, :, :3] * 255).astype(np.uint8)
        h, _, _ = rgba.shape
        img = QImage(rgba.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        self._pix = QPixmap.fromImage(img).scaled(
            self.width(), self.height(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(self._pix)

    def resizeEvent(self, e):
        self.set_cmap(self._name)
        super().resizeEvent(e)


# ============================================================
# Main window
# ============================================================
class ChaosGameMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Game Fractal Generator")
        self.setMinimumSize(1050, 700)
        self.resize(1380, 880)

        # State
        self.data: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
        self.verts: Optional[list] = None
        self.cfg: Optional[Dict[str, Any]] = None
        self._xlim = (-1.3, 1.3)
        self._ylim = (-1.3, 1.3)
        self._anim_timer: Optional[QTimer] = None
        self._anim_img: Optional[np.ndarray] = None
        self._anim_lut: Optional[np.ndarray] = None
        self._anim_end = 0
        self._anim_batch = 0
        self._anim_px: Optional[np.ndarray] = None
        self._anim_py: Optional[np.ndarray] = None
        self._anim_mask: Optional[np.ndarray] = None
        self._prog_timer: Optional[QTimer] = None

        self._apply_theme()
        self._build_ui()
        self._connect()

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+G"), self, self._generate)
        QShortcut(QKeySequence("Escape"), self, self._stop_anim)

        if PRESETS:
            self._apply_preset(0)

    # --------------------------------------------------------
    # Theme
    # --------------------------------------------------------
    def _apply_theme(self):
        self.setStyleSheet(f"""
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
        """)

    # --------------------------------------------------------
    # UI construction
    # --------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # === Sidebar ===
        sb = QWidget()
        sb.setFixedWidth(300)
        sb.setStyleSheet(f"border-right:1px solid {C['border']};")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(8, 8, 8, 8)
        sbl.setSpacing(5)

        title = QLabel("Chaos Game\nFractal Generator")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color:{C['accent']};padding:4px 0 2px 0;")
        title.setAlignment(Qt.AlignCenter)
        sbl.addWidget(title)

        tabs = QTabWidget()
        sbl.addWidget(tabs, 1)

        # -- Presets tab --
        pt = QWidget()
        ptl = QVBoxLayout(pt)
        ptl.setContentsMargins(0, 0, 0, 0)
        self.gallery = GalleryWidget()
        ptl.addWidget(self.gallery)
        tabs.addTab(pt, "Presets")

        # -- Custom tab --
        co = QScrollArea()
        co.setWidgetResizable(True)
        co.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        co.setStyleSheet(f"""
            QScrollArea {{border:none;background:transparent;}}
            QScrollBar:vertical {{
                background:{C['bg1']};width:4px;border-radius:2px;
            }}
            QScrollBar::handle:vertical {{
                background:{C['bg4']};border-radius:2px;min-height:12px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{height:0;}}
        """)
        ct = QWidget()
        co.setWidget(ct)
        tabs.addTab(co, "Custom")

        cl = QVBoxLayout(ct)
        cl.setSpacing(7)
        cl.setContentsMargins(6, 6, 6, 6)

        # Geometry group
        geo = QGroupBox("Geometry")
        gg = QGridLayout(geo)
        gg.setSpacing(5)

        gg.addWidget(QLabel("Vertices:"), 0, 0)
        self.sp_vert = QSpinBox()
        self.sp_vert.setRange(3, 64)
        self.sp_vert.setValue(5)
        gg.addWidget(self.sp_vert, 0, 1)

        gg.addWidget(QLabel("Ratio (r):"), 1, 0)
        self.sp_ratio = QDoubleSpinBox()
        self.sp_ratio.setRange(0.01, 0.99)
        self.sp_ratio.setValue(0.5)
        self.sp_ratio.setSingleStep(0.01)
        self.sp_ratio.setDecimals(4)
        gg.addWidget(self.sp_ratio, 1, 1)

        self.chk_rand_r = QCheckBox("Random ratio per step")
        self.chk_rand_r.stateChanged.connect(
            lambda s: self.sp_ratio.setEnabled(s == Qt.Unchecked))
        gg.addWidget(self.chk_rand_r, 2, 0, 1, 2)

        gg.addWidget(QLabel("Skip:"), 3, 0)
        self.sp_skip = QSpinBox()
        self.sp_skip.setRange(0, 30)
        self.sp_skip.setValue(0)
        self.sp_skip.setToolTip(
            "Min circular vertex distance.\n0 = no constraint")
        gg.addWidget(self.sp_skip, 3, 1)

        self.chk_rv = QCheckBox("Random vertex positions")
        gg.addWidget(self.chk_rv, 4, 0, 1, 2)

        self.chk_nr = QCheckBox("No consecutive repeat")
        gg.addWidget(self.chk_nr, 5, 0, 1, 2)

        cl.addWidget(geo)

        # Rendering group
        ren = QGroupBox("Rendering")
        rg = QGridLayout(ren)
        rg.setSpacing(5)

        rg.addWidget(QLabel("Points:"), 0, 0)
        self.sl_pts = QSlider(Qt.Horizontal)
        self.sl_pts.setRange(5_000, 1_000_000)
        self.sl_pts.setValue(200_000)
        self.sl_pts.setSingleStep(10_000)
        rg.addWidget(self.sl_pts, 0, 1)
        self.lb_pts = QLabel("200,000")
        self.lb_pts.setFixedWidth(62)
        self.lb_pts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rg.addWidget(self.lb_pts, 0, 2)
        self.sl_pts.valueChanged.connect(
            lambda v: self.lb_pts.setText(f"{v:,}"))

        rg.addWidget(QLabel("Point size:"), 1, 0)
        self.sl_ps = QSlider(Qt.Horizontal)
        self.sl_ps.setRange(1, 300)
        self.sl_ps.setValue(10)
        rg.addWidget(self.sl_ps, 1, 1)
        self.lb_ps = QLabel("0.10")
        self.lb_ps.setFixedWidth(62)
        self.lb_ps.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rg.addWidget(self.lb_ps, 1, 2)
        self.sl_ps.valueChanged.connect(
            lambda v: self.lb_ps.setText(f"{v / 100:.2f}"))

        rg.addWidget(QLabel("Palette:"), 2, 0)
        self.cb_cmap = QComboBox()
        self.cb_cmap.addItems(COLORMAPS)
        self.cb_cmap.setCurrentText("turbo")
        rg.addWidget(self.cb_cmap, 2, 1, 1, 2)

        self.cmap_prev = CmapPreviewWidget()
        rg.addWidget(self.cmap_prev, 3, 0, 1, 3)
        self.cb_cmap.currentTextChanged.connect(self.cmap_prev.set_cmap)

        rg.addWidget(QLabel("Seed:"), 4, 0)
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(-1, 999999)
        self.sp_seed.setValue(-1)
        self.sp_seed.setToolTip("-1 = random each time")
        rg.addWidget(self.sp_seed, 4, 1)
        self.lb_seed = QLabel("(random)")
        self.lb_seed.setStyleSheet(f"color:{C['text3']};font-size:9px;")
        rg.addWidget(self.lb_seed, 4, 2)
        self.sp_seed.valueChanged.connect(
            lambda v: self.lb_seed.setText(
                "(random)" if v < 0 else str(v)))

        cl.addWidget(ren)

        # Reference group
        info = QGroupBox("Quick Reference")
        il = QVBoxLayout(info)
        il.setSpacing(1)
        ref = QLabel(
            "• r=0.5, skip=0 → classic fill\n"
            "• no_repeat → no same vertex twice\n"
            "• skip≥1 → star / void patterns\n"
            "• r≈0.618 → golden ratio fractals\n"
            "• random r → organic cloud shapes\n"
            "• random vertices → irregular polygons\n"
            "• Ctrl+G → generate  |  Esc → stop anim"
        )
        ref.setWordWrap(True)
        ref.setStyleSheet(f"color:{C['text3']};font-size:9px;")
        il.addWidget(ref)
        cl.addWidget(info)
        cl.addStretch()

        # Action buttons
        blo = QVBoxLayout()
        blo.setSpacing(4)

        self.btn_gen = QPushButton("⚡  Generate Fractal")
        self.btn_gen.setStyleSheet(f"""
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
        """)
        blo.addWidget(self.btn_gen)

        r1 = QHBoxLayout()
        self.btn_anim = QPushButton("▶  Animate")
        self.btn_stop = QPushButton("⏹  Stop")
        self.btn_stop.setEnabled(False)
        r1.addWidget(self.btn_anim)
        r1.addWidget(self.btn_stop)
        blo.addLayout(r1)

        r2 = QHBoxLayout()
        self.btn_png = QPushButton("PNG")
        self.btn_gif = QPushButton("GIF")
        self.btn_verts = QPushButton("Vertices")
        r2.addWidget(self.btn_png)
        r2.addWidget(self.btn_gif)
        r2.addWidget(self.btn_verts)
        blo.addLayout(r2)

        self.btn_clr = QPushButton("Clear Canvas")
        self.btn_clr.setStyleSheet(f"""
            QPushButton {{
                background: {C['bg0']};
                border-color: #3a1a2e;
                color: {C['rose']};
            }}
            QPushButton:hover {{
                background: #1a0e14;
                border-color: #5a2a4e;
            }}
        """)
        blo.addWidget(self.btn_clr)
        sbl.addLayout(blo)

        self.prog = QProgressBar()
        self.prog.setVisible(False)
        sbl.addWidget(self.prog)

        # === Canvas area ===
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.canvas = FractalCanvas(self, width=8, height=8, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {C['bg0']};
                border-bottom: 1px solid {C['border']};
                spacing: 2px;
                padding: 1px;
            }}
            QToolButton {{
                background: {C['bg2']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                padding: 3px 6px;
                color: {C['text2']};
                font-size: 10px;
            }}
            QToolButton:hover {{
                background: {C['bg3']};
                border-color: {C['accent']};
            }}
        """)

        rl.addWidget(self.toolbar)
        rl.addWidget(self.canvas, 1)

        root.addWidget(sb)
        root.addWidget(right, 1)

        self.statusBar().showMessage(
            "Ready — choose a preset or set custom parameters, then Generate")

    # --------------------------------------------------------
    # Signals
    # --------------------------------------------------------
    def _connect(self):
        self.gallery.preset_selected.connect(self._apply_preset)
        self.btn_gen.clicked.connect(self._generate)
        self.btn_anim.clicked.connect(self._start_anim)
        self.btn_stop.clicked.connect(self._stop_anim)
        self.btn_png.clicked.connect(self._save_png)
        self.btn_gif.clicked.connect(self._save_gif)
        self.btn_verts.clicked.connect(self._show_verts)
        self.btn_clr.clicked.connect(self._clear)

    # --------------------------------------------------------
    # Preset loading
    # --------------------------------------------------------
    def _apply_preset(self, idx):
        if not (0 <= idx < len(PRESETS)):
            return
        p = PRESETS[idx]
        self.sp_vert.setValue(p["vertices"])
        r = p.get("r")
        if r is None:
            self.chk_rand_r.setChecked(True)
            self.sp_ratio.setValue(0.5)
        else:
            self.chk_rand_r.setChecked(False)
            self.sp_ratio.setValue(r)
        self.sp_skip.setValue(p.get("skip", 0))
        self.chk_rv.setChecked(p.get("random_vertices", False))
        self.chk_nr.setChecked(p.get("no_repeat", False))
        self.cb_cmap.setCurrentText(p.get("colormap", "turbo"))
        self.sl_ps.setValue(p.get("point_size", 10))
        self.statusBar().showMessage(f"Loaded preset: {p['title']}")

    def _get_cfg(self) -> Dict[str, Any]:
        return {
            "vertices": self.sp_vert.value(),
            "r": None if self.chk_rand_r.isChecked() else self.sp_ratio.value(),
            "skip": self.sp_skip.value(),
            "random_vertices": self.chk_rv.isChecked(),
            "no_repeat": self.chk_nr.isChecked(),
            "colormap": self.cb_cmap.currentText(),
            "point_size": self.sl_ps.value() / 100.0,
        }

    @staticmethod
    def _make_title(cfg) -> str:
        r_s = "rand" if cfg["r"] is None else f"r={cfg['r']:.3f}"
        parts = [f"{cfg['vertices']}-gon", r_s]
        if cfg["skip"]:
            parts.append(f"skip={cfg['skip']}")
        if cfg["no_repeat"]:
            parts.append("no-repeat")
        if cfg["random_vertices"]:
            parts.append("irregular")
        return "  ·  ".join(parts)

    # --------------------------------------------------------
    # Generation
    # --------------------------------------------------------
    def _generate(self):
        cfg = self._get_cfg()
        iters = self.sl_pts.value()
        seed = self.sp_seed.value() if self.sp_seed.value() >= 0 else None

        self._stop_anim()
        self.btn_gen.setEnabled(False)
        self.btn_anim.setEnabled(False)
        self.prog.setVisible(True)
        self.prog.setValue(0)
        self.statusBar().showMessage("Generating…")

        self._worker = GenerationWorker(cfg, iters, seed)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_err)
        self._worker.start()

        self._pv = 0
        self._prog_timer = QTimer()
        self._prog_timer.timeout.connect(self._tick)
        self._prog_timer.start(35)

    def _tick(self):
        self._pv = min(self._pv + 1, 93)
        self.prog.setValue(self._pv)

    def _on_done(self, xs, ys, colors, elapsed, verts):
        self._prog_timer.stop()
        self.prog.setValue(100)
        QTimer.singleShot(350, self.prog.hide)

        self.data = (xs, ys, colors)
        self.verts = verts
        self.cfg = self._get_cfg()
        cfg = self.cfg

        # Compute tight bounds
        self._xlim, self._ylim = BitmapRenderer.compute_bounds(xs, ys)
        self.canvas.set_extent(self._xlim, self._ylim)

        if len(xs) <= SCATTER_THRESHOLD:
            self.canvas.plot_scatter(
                xs, ys, colors,
                cfg["colormap"], cfg["point_size"],
                self._make_title(cfg))
        else:
            bmp = BitmapRenderer.render(
                xs, ys, colors,
                DISPLAY_RES, DISPLAY_RES,
                self._xlim, self._ylim,
                cfg["colormap"], BG_RGB)
            self.canvas.show_bitmap(bmp, self._make_title(cfg))

        self.btn_gen.setEnabled(True)
        self.btn_anim.setEnabled(True)
        r_s = "random" if cfg["r"] is None else f"{cfg['r']:.4f}"
        self.statusBar().showMessage(
            f"{len(xs):,} pts in {elapsed:.2f}s  |  "
            f"v={cfg['vertices']}  r={r_s}  skip={cfg['skip']}")

    def _on_err(self, msg):
        self._prog_timer.stop()
        self.prog.hide()
        self.btn_gen.setEnabled(True)
        self.btn_anim.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Generation failed:\n{msg}")

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------
    def _start_anim(self):
        if self.data is None:
            self.statusBar().showMessage("Generate a fractal first!")
            return

        xs, ys, colors = self.data
        total = len(xs)
        cfg = self.cfg
        w, h = ANIM_RES, ANIM_RES

        self._anim_end = 0
        self._anim_batch = max(3000, total // 100)

        # Pre-compute all pixel positions once
        self._anim_px, self._anim_py, self._anim_mask = \
            BitmapRenderer.precompute_pixels(xs, ys, w, h, self._xlim, self._ylim)
        self._anim_colors_filtered = colors[self._anim_mask]

        # Build LUT
        c_max = max(int(colors.max()), 1)
        self._anim_lut = BitmapRenderer._build_lut(cfg["colormap"], c_max)

        # Start with blank image
        self._anim_img = np.full((h, w, 3), BG_RGB, dtype=np.uint8)

        # Set up canvas
        self.canvas.set_extent(self._xlim, self._ylim)
        self.canvas.ax.clear()
        self.canvas._setup()
        self.canvas._img_artist = self.canvas.ax.imshow(
            self._anim_img, aspect="equal", interpolation="bilinear",
            extent=self.canvas._extent, origin="upper")
        self.canvas.ax.set_title(
            f"0 / {total:,}", fontsize=11, color=C["text"],
            pad=6, fontweight="bold", fontfamily="monospace")
        self.canvas.fig.subplots_adjust(
            left=0.01, right=0.99, top=0.95, bottom=0.01)
        self.canvas.draw()

        self.btn_anim.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_gen.setEnabled(False)

        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(33)
        self.statusBar().showMessage("Animating…")

    def _anim_tick(self):
        xs, ys, colors = self.data
        total = len(xs)
        w, h = ANIM_RES, ANIM_RES

        start = self._anim_end
        end = min(start + self._anim_batch, total)

        # Slice the pre-computed filtered arrays
        # We need to map `end` (index into original data) to index into
        # the filtered (masked) arrays. Count how many masked points are <= end.
        # More efficient: precompute cumulative mask
        if not hasattr(self, '_anim_cumsum'):
            self._anim_cumsum = np.cumsum(self._anim_mask)
        # Number of valid points up to `end` in original array
        e_filtered = int(self._anim_cumsum[min(end, total - 1)])

        if e_filtered > 0:
            px_batch = self._anim_px[start_filt:e_filtered] if hasattr(self, '_start_filt') else self._anim_px[:e_filtered]
            # Fix: always index from 0 in filtered arrays
            px_batch = self._anim_px[:e_filtered]
            py_batch = self._anim_py[:e_filtered]
            c_batch = self._anim_colors_filtered[:e_filtered]
            self._anim_img[py_batch, px_batch] = self._anim_lut[c_batch]

        self._anim_end = end
        self.canvas._img_artist.set_data(self._anim_img)
        self.canvas.ax.set_title(
            f"{end:,} / {total:,}", fontsize=11, color=C["text"],
            pad=6, fontweight="bold", fontfamily="monospace")
        self.canvas.draw_idle()

        if end >= total:
            self._stop_anim()
            # Render final high-quality frame with glow
            bmp = BitmapRenderer.render(
                xs, ys, colors,
                DISPLAY_RES, DISPLAY_RES,
                self._xlim, self._ylim,
                self.cfg["colormap"], BG_RGB)
            self.canvas.show_bitmap(bmp, self._make_title(self.cfg))
            self.statusBar().showMessage(
                f"Animation complete — {total:,} points")

    def _stop_anim(self):
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None
        # Clean up animation-specific cached data
        for attr in ('_anim_img', '_anim_lut', '_anim_px', '_anim_py',
                      '_anim_mask', '_anim_colors_filtered', '_anim_cumsum'):
            if hasattr(self, attr):
                delattr(self, attr)
        self.btn_anim.setEnabled(self.data is not None)
        self.btn_stop.setEnabled(False)
        self.btn_gen.setEnabled(True)

    # --------------------------------------------------------
    # Save PNG
    # --------------------------------------------------------
    def _save_png(self):
        if self.data is None:
            QMessageBox.information(self, "No Data", "Generate first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PNG", "fractal.png", "PNG (*.png)")
        if not path:
            return

        self.statusBar().showMessage("Rendering high-res PNG…")
        QApplication.processEvents()

        xs, ys, colors = self.data
        bmp = BitmapRenderer.render(
            xs, ys, colors,
            EXPORT_RES, EXPORT_RES,
            self._xlim, self._ylim,
            self.cfg["colormap"], BG_RGB)
        h, w, _ = bmp.shape
        img = QImage(bmp.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        img.save(path, quality=95)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        self.statusBar().showMessage(f"Saved: {path}  ({size_mb:.1f} MB)")

    # --------------------------------------------------------
    # Save GIF
    # --------------------------------------------------------
    def _save_gif(self):
        if self.data is None:
            QMessageBox.information(self, "No Data", "Generate first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "fractal.gif", "GIF (*.gif)")
        if not path:
            return

        self.statusBar().showMessage("Generating GIF — please wait…")
        self.btn_gif.setEnabled(False)
        QApplication.processEvents()

        try:
            xs, ys, colors = self.data
            total = len(xs)
            cfg = self.cfg
            gw, gh = 800, 800
            n_frames = 60
            batch = max(1, total // n_frames)

            fig, ax = plt.subplots(
                figsize=(6, 6), dpi=80, facecolor=C["canvas_bg"])
            ax.set_facecolor(C["canvas_bg"])
            ax.axis("off")
            ax.set_aspect("equal")
            fig.subplots_adjust(
                left=0.01, right=0.99, top=0.96, bottom=0.01)

            blank = np.full((gh, gw, 3), BG_RGB, dtype=np.uint8)
            im = ax.imshow(blank, aspect="equal", interpolation="bilinear",
                           extent=list(self._xlim) + list(self._ylim),
                           origin="upper")
            info = ax.text(
                0.5, 0.98, "", ha="center", va="top",
                transform=fig.transFigure, fontsize=9,
                color=C["text"], fontweight="bold", fontfamily="monospace")

            # Pre-build LUT
            c_max = max(int(colors.max()), 1)
            lut = BitmapRenderer._build_lut(cfg["colormap"], c_max)

            # Pre-compute all pixel positions
            all_px, all_py, mask_all = BitmapRenderer.precompute_pixels(
                xs, ys, gw, gh, self._xlim, self._ylim)
            all_px = all_px
            all_py = all_py
            all_c = colors[mask_all]
            n_valid = len(all_px)

            running = np.full((gh, gw, 3), BG_RGB, dtype=np.uint8)

            def update(frame):
                end_orig = min((frame + 1) * batch, total)
                # Map original end index to filtered index
                end_filt = min(int(np.searchsorted(
                    np.cumsum(mask_all), end_orig, side="right")), n_valid)
                if end_filt > 0:
                    running[all_py[:end_filt],
                            all_px[:end_filt]] = lut[all_c[:end_filt]]
                im.set_data(running)
                info.set_text(f"{end_orig:,} / {total:,} pts")
                return im, info

            anim = FuncAnimation(
                fig, update, frames=n_frames, interval=50, blit=True)
            anim.save(path, writer=PillowWriter(fps=20), dpi=80)
            plt.close(fig)

            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.statusBar().showMessage(
                f"GIF saved: {path}  ({size_mb:.1f} MB)")

        except Exception as e:
            QMessageBox.critical(self, "GIF Error", str(e))
            self.statusBar().showMessage("GIF generation failed")
        finally:
            self.btn_gif.setEnabled(True)

    # --------------------------------------------------------
    # Vertices overlay
    # --------------------------------------------------------
    def _show_verts(self):
        if self.verts is None:
            self.statusBar().showMessage("Generate a fractal first!")
            return
        self.canvas.plot_vertices(self.verts)
        self.statusBar().showMessage("Vertex overlay shown")

    # --------------------------------------------------------
    # Clear
    # --------------------------------------------------------
    def _clear(self):
        self._stop_anim()
        self.data = None
        self.verts = None
        self.cfg = None
        self._xlim = (-1.3, 1.3)
        self._ylim = (-1.3, 1.3)
        self.canvas.clear_plot()
        self.statusBar().showMessage("Canvas cleared")

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------
    def closeEvent(self, event):
        self._stop_anim()
        if self._prog_timer is not None:
            self._prog_timer.stop()
        if hasattr(self, "_worker") and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)
        event.accept()


# ============================================================
# Entry point
# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Chaos Game Fractal Generator")
    window = ChaosGameMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()