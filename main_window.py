"""
Chaos Game Fractal Generator — Main Window
Enhanced with resolution options, palette controls, and visibility settings
"""

import os
import sys
import logging
from typing import Optional, Tuple
import numpy as np

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QComboBox, QSlider, QGroupBox, QScrollArea, QFileDialog,
    QProgressBar, QTabWidget, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QShortcut, QKeySequence

from config import (
    C, BG_RGB, PRESETS, EXPORT_RES, ANIM_RES,
    SCATTER_THRESHOLD, COLORMAPS, RESOLUTION_PRESETS,
    POINTS_DENSITY, DEFAULT_DISPLAY_RES
)
from theme import STYLESHEET, GENERATE_BUTTON_STYLE, CLEAR_BUTTON_STYLE, SCROLL_STYLE
from canvas import FractalCanvas
from widgets import GalleryWidget, CmapPreviewWidget
from compute_backend import BitmapRenderer, HAS_CUPY, get_backend_info
from worker import GenerationWorker, GifWorker

logger = logging.getLogger("UI")


class ChaosGameMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Game Fractal Generator")
        self.setMinimumSize(1050, 750)
        self.resize(1450, 920)

        self.data = None
        self.verts = None
        self.cfg = None
        self._xlim = (-1.3, 1.3)
        self._ylim = (-1.3, 1.3)

        # Animation state
        self._anim_timer = None
        self._anim_img = None
        self._anim_lut = None
        self._anim_end = 0
        self._anim_batch = 0
        self._anim_px = None
        self._anim_py = None
        self._anim_mask = None
        self._anim_colors = None
        self._anim_cumsum = None

        # Progress & workers
        self._prog_timer = None
        self._prog_val = 0
        self._worker = None
        self._gif_worker = None

        self._apply_theme()
        self._build_ui()
        self._connect()

        QShortcut(QKeySequence("Ctrl+G"), self, self._generate)
        QShortcut(QKeySequence("Escape"), self, self._stop_anim)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_png)

        # Auto-load first preset
        if PRESETS:
            self._apply_preset(0)

    # ------------------------------------------------------------------ theme
    def _apply_theme(self):
        self.setStyleSheet(STYLESHEET)

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ---- LEFT SIDEBAR ----
        sb = QWidget()
        sb.setFixedWidth(320)
        sb.setStyleSheet(f"border-right:1px solid {C['border']};")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(8, 8, 8, 8)
        sbl.setSpacing(5)

        title = QLabel("Chaos Game\nFractal Generator")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color:{C['accent']};padding:4px 0 2px 0;")
        title.setAlignment(Qt.AlignCenter)
        sbl.addWidget(title)

        backend_lbl = QLabel(get_backend_info())
        backend_lbl.setAlignment(Qt.AlignCenter)
        backend_lbl.setStyleSheet(
            f"color:{C['text3']};font-size:8px;padding:0 0 4px 0;"
        )
        sbl.addWidget(backend_lbl)

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
        co.setStyleSheet(SCROLL_STYLE)
        ct = QWidget()
        co.setWidget(ct)
        tabs.addTab(co, "Custom")

        cl = QVBoxLayout(ct)
        cl.setSpacing(7)
        cl.setContentsMargins(6, 6, 6, 6)

        # ========== Resolution Group ==========
        res_grp = QGroupBox("Resolution")
        rg = QGridLayout(res_grp)
        rg.setSpacing(5)

        rg.addWidget(QLabel("Display:"), 0, 0)
        self.cb_resolution = QComboBox()
        self.cb_resolution.addItems(RESOLUTION_PRESETS.keys())
        self.cb_resolution.setCurrentText("1024 × 1024")
        self.cb_resolution.currentTextChanged.connect(self._on_resolution_changed)
        rg.addWidget(self.cb_resolution, 0, 1)

        self.lb_res_info = QLabel("250K pts recommended")
        self.lb_res_info.setStyleSheet(f"color:{C['text3']};font-size:9px;")
        rg.addWidget(self.lb_res_info, 1, 0, 1, 2)

        self.chk_auto_pts = QCheckBox("Auto-adjust points for resolution")
        self.chk_auto_pts.setChecked(True)
        rg.addWidget(self.chk_auto_pts, 2, 0, 1, 2)

        cl.addWidget(res_grp)

        # ========== Geometry Group ==========
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
            lambda s: self.sp_ratio.setEnabled(s == Qt.Unchecked)
        )
        gg.addWidget(self.chk_rand_r, 2, 0, 1, 2)

        gg.addWidget(QLabel("Skip:"), 3, 0)
        self.sp_skip = QSpinBox()
        self.sp_skip.setRange(0, 30)
        self.sp_skip.setValue(0)
        gg.addWidget(self.sp_skip, 3, 1)

        self.chk_rv = QCheckBox("Random vertex positions")
        gg.addWidget(self.chk_rv, 4, 0, 1, 2)

        self.chk_nr = QCheckBox("No consecutive repeat")
        gg.addWidget(self.chk_nr, 5, 0, 1, 2)

        cl.addWidget(geo)

        # ========== Rendering Group ==========
        ren = QGroupBox("Rendering & Visuals")
        rg2 = QGridLayout(ren)
        rg2.setSpacing(5)

        rg2.addWidget(QLabel("Points:"), 0, 0)
        self.sl_pts = QSlider(Qt.Horizontal)
        self.sl_pts.setRange(10_000, 3_000_000)
        self.sl_pts.setValue(250_000)
        self.sl_pts.setSingleStep(10_000)
        rg2.addWidget(self.sl_pts, 0, 1)
        self.lb_pts = QLabel("250,000")
        self.lb_pts.setFixedWidth(65)
        self.lb_pts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rg2.addWidget(self.lb_pts, 0, 2)
        self.sl_pts.valueChanged.connect(
            lambda v: self.lb_pts.setText(f"{v:,}")
        )

        rg2.addWidget(QLabel("Palette:"), 1, 0)
        self.cb_cmap = QComboBox()
        for cmap_name in COLORMAPS:
            if cmap_name.startswith("--"):
                self.cb_cmap.insertSeparator(self.cb_cmap.count())
            else:
                self.cb_cmap.addItem(cmap_name)
        self.cb_cmap.setCurrentText("Neon")
        rg2.addWidget(self.cb_cmap, 1, 1, 1, 2)

        self.cmap_prev = CmapPreviewWidget()
        rg2.addWidget(self.cmap_prev, 2, 0, 1, 3)
        self.cb_cmap.currentTextChanged.connect(self._on_cmap_changed)

        rg2.addWidget(QLabel("Mode:"), 3, 0)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems([
            "Vibrant (Direct)", "Smooth (Averaged)", "Glow (Soft)"
        ])
        rg2.addWidget(self.cb_mode, 3, 1, 1, 2)

        cl.addWidget(ren)

        # ========== Visibility Enhancements Group ==========
        vis = QGroupBox("Visibility Enhancements")
        vg = QGridLayout(vis)
        vg.setSpacing(5)

        vg.addWidget(QLabel("Brightness:"), 0, 0)
        self.sl_brightness = QSlider(Qt.Horizontal)
        self.sl_brightness.setRange(0, 100)
        self.sl_brightness.setValue(30)  # Changed from 20 to 30
        vg.addWidget(self.sl_brightness, 0, 1)
        self.lb_brightness = QLabel("30%")  # Changed from 20%
        self.lb_brightness.setFixedWidth(65)
        self.lb_brightness.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vg.addWidget(self.lb_brightness, 0, 2)
        self.sl_brightness.valueChanged.connect(
            lambda v: self.lb_brightness.setText(f"{v}%")
        )

        vg.addWidget(QLabel("Gamma:"), 1, 0)
        self.sl_gamma = QSlider(Qt.Horizontal)
        self.sl_gamma.setRange(50, 200)  # 0.5 to 2.0
        self.sl_gamma.setValue(90)  # Changed from 100 to 90 (slightly brighter)
        vg.addWidget(self.sl_gamma, 1, 1)
        self.lb_gamma = QLabel("0.90")  # Changed from 1.00
        self.lb_gamma.setFixedWidth(65)
        self.lb_gamma.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vg.addWidget(self.lb_gamma, 1, 2)
        self.sl_gamma.valueChanged.connect(
            lambda v: self.lb_gamma.setText(f"{v/100:.2f}")
        )

        vg.addWidget(QLabel("Vibrancy:"), 2, 0)
        self.sl_vib = QSlider(Qt.Horizontal)
        self.sl_vib.setRange(0, 100)
        self.sl_vib.setValue(40)  # Changed from 30 to 40
        vg.addWidget(self.sl_vib, 2, 1)
        self.lb_vib = QLabel("1.4x")  # Changed from 1.3x
        self.lb_vib.setFixedWidth(65)
        self.lb_vib.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vg.addWidget(self.lb_vib, 2, 2)
        self.sl_vib.valueChanged.connect(
            lambda v: self.lb_vib.setText(f"{1.0 + (v / 100.0):.1f}x")
        )

        vg.addWidget(QLabel("Point size:"), 3, 0)
        self.sl_ps = QSlider(Qt.Horizontal)
        self.sl_ps.setRange(1, 300)
        self.sl_ps.setValue(10)
        vg.addWidget(self.sl_ps, 3, 1)
        self.lb_ps = QLabel("0.10")
        self.lb_ps.setFixedWidth(65)
        self.lb_ps.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vg.addWidget(self.lb_ps, 3, 2)
        self.sl_ps.valueChanged.connect(
            lambda v: self.lb_ps.setText(f"{v / 100:.2f}")
        )

        self.chk_invert = QCheckBox("Invert palette")
        vg.addWidget(self.chk_invert, 4, 0, 1, 2)

        self.chk_adaptive = QCheckBox("Adaptive brightness")
        self.chk_adaptive.setChecked(True)
        vg.addWidget(self.chk_adaptive, 4, 2, 1, 1)

        self.chk_dilate2x = QCheckBox("2x dilation (sparse fractals)")
        vg.addWidget(self.chk_dilate2x, 5, 0, 1, 3)

        cl.addWidget(vis)

        # ========== Advanced Group ==========
        adv = QGroupBox("Advanced")
        ag = QGridLayout(adv)
        ag.setSpacing(5)

        ag.addWidget(QLabel("Seed:"), 0, 0)
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(-1, 999999)
        self.sp_seed.setValue(-1)
        ag.addWidget(self.sp_seed, 0, 1)
        self.lb_seed = QLabel("(random)")
        self.lb_seed.setStyleSheet(f"color:{C['text3']};font-size:9px;")
        ag.addWidget(self.lb_seed, 0, 2)
        self.sp_seed.valueChanged.connect(
            lambda v: self.lb_seed.setText("(random)" if v < 0 else str(v))
        )

        self.chk_gpu = QCheckBox("Use GPU (CuPy)")
        self.chk_gpu.setChecked(HAS_CUPY)
        self.chk_gpu.setEnabled(HAS_CUPY)
        ag.addWidget(self.chk_gpu, 1, 0, 1, 3)

        cl.addWidget(adv)

        # Quick reference
        info = QGroupBox("Quick Reference")
        il = QVBoxLayout(info)
        il.setSpacing(1)
        ref = QLabel(
            "• Scroll: Zoom in/out\n"
            "• Double-Click: Reset view\n"
            "• Ctrl+G: Generate | Esc: Stop\n"
            "• Ctrl+S: Save PNG"
        )
        ref.setWordWrap(True)
        ref.setStyleSheet(f"color:{C['text3']};font-size:9px;")
        il.addWidget(ref)
        cl.addWidget(info)
        cl.addStretch()

        # ---- BUTTONS ----
        blo = QVBoxLayout()
        blo.setSpacing(4)

        self.btn_gen = QPushButton("⚡  Generate Fractal")
        self.btn_gen.setStyleSheet(GENERATE_BUTTON_STYLE)
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
        self.btn_clr.setStyleSheet(CLEAR_BUTTON_STYLE)
        blo.addWidget(self.btn_clr)

        sbl.addLayout(blo)

        self.prog = QProgressBar()
        self.prog.setVisible(False)
        sbl.addWidget(self.prog)

        # ---- RIGHT: CANVAS ----
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        self.canvas = FractalCanvas(self, width=8, height=8, dpi=100)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rl.addWidget(self.canvas, 1)

        root.addWidget(sb)
        root.addWidget(right, 1)

        self.statusBar().showMessage(
            "Ready — Scroll to zoom, Double-click to reset"
        )

    # ---------------------------------------------------------------- connect
    def _connect(self):
        self.gallery.preset_selected.connect(self._apply_preset)
        self.btn_gen.clicked.connect(self._generate)
        self.btn_anim.clicked.connect(self._start_anim)
        self.btn_stop.clicked.connect(self._stop_anim)
        self.btn_png.clicked.connect(self._save_png)
        self.btn_gif.clicked.connect(self._save_gif)
        self.btn_verts.clicked.connect(self._show_verts)
        self.btn_clr.clicked.connect(self._clear)

    # ----------------------------------------------------------- helpers
    def _on_resolution_changed(self, text):
        res = RESOLUTION_PRESETS.get(text, 1024)
        recommended = POINTS_DENSITY.get(res, 250_000)
        self.lb_res_info.setText(f"{recommended:,} pts recommended")
        
        if self.chk_auto_pts.isChecked():
            self.sl_pts.setValue(recommended)

    def _on_cmap_changed(self, name):
        if not name.startswith("--"):
            self.cmap_prev.set_cmap(name)

    def _get_resolution(self):
        text = self.cb_resolution.currentText()
        return RESOLUTION_PRESETS.get(text, DEFAULT_DISPLAY_RES)

    # ------------------------------------------------------------- presets
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
        self.cb_cmap.setCurrentText(p.get("colormap", "Neon"))
        self.sl_ps.setValue(p.get("point_size", 10))
        
        # Set resolution from preset
        preset_res = p.get("resolution", 1024)
        res_text = f"{preset_res} × {preset_res}"
        if res_text in RESOLUTION_PRESETS:
            self.cb_resolution.setCurrentText(res_text)
        
        logger.info(f"Loaded preset: {p['title']}")

    # ---------------------------------------------------------- config helpers
    def _get_cfg(self):
        return {
            "vertices": self.sp_vert.value(),
            "r": None if self.chk_rand_r.isChecked() else self.sp_ratio.value(),
            "skip": self.sp_skip.value(),
            "random_vertices": self.chk_rv.isChecked(),
            "no_repeat": self.chk_nr.isChecked(),
            "colormap": self.cb_cmap.currentText(),
            "point_size": self.sl_ps.value() / 100.0,
        }

    def _get_visual_cfg(self):
        return {
            "mode": self.cb_mode.currentText(),
            "vibrancy_factor": 1.0 + (self.sl_vib.value() / 100.0),
            "use_gpu": self.chk_gpu.isChecked(),
            "brightness_boost": self.sl_brightness.value() / 100.0,
            "gamma": self.sl_gamma.value() / 100.0,
            "invert": self.chk_invert.isChecked(),
            "adaptive_eq": self.chk_adaptive.isChecked(),
            "dilate_2x": self.chk_dilate2x.isChecked(),
        }

    @staticmethod
    def _make_title(cfg, res=1024):
        r_s = "rand" if cfg["r"] is None else f"r={cfg['r']:.3f}"
        parts = [f"{cfg['vertices']}-gon", r_s, f"{res}px"]
        if cfg["skip"]:
            parts.append(f"skip={cfg['skip']}")
        if cfg["no_repeat"]:
            parts.append("no-repeat")
        if cfg["random_vertices"]:
            parts.append("irregular")
        return "  ·  ".join(parts)

    # ----------------------------------------------------------- rendering
    def _render_fractal_bitmap(self, xs, ys, colors, cfg, vis_cfg,
                               res=None):
        if res is None:
            res = self._get_resolution()
            
        xlim, ylim = self._xlim, self._ylim
        cmap, mode = cfg["colormap"], vis_cfg["mode"]
        vib, gpu = vis_cfg["vibrancy_factor"], vis_cfg["use_gpu"]
        brightness = vis_cfg["brightness_boost"]
        gamma = vis_cfg["gamma"]
        invert = vis_cfg["invert"]
        adaptive = vis_cfg["adaptive_eq"]
        dilate2x = vis_cfg["dilate_2x"]

        render_kwargs = {
            "cmap_name": cmap,
            "brightness_boost": brightness,
            "gamma": gamma,
            "invert": invert,
        }

        if "Vibrant" in mode:
            bmp = BitmapRenderer.render_direct(
                xs, ys, colors, res, res, xlim, ylim, **render_kwargs
            )
            dilate_iter = 2 if dilate2x else 1
            bmp = BitmapRenderer.dilate(bmp, use_gpu=gpu, iterations=dilate_iter)
        elif "Smooth" in mode:
            bmp = BitmapRenderer.render(
                xs, ys, colors, res, res, xlim, ylim,
                glow=False, use_gpu=gpu, adaptive_eq=adaptive,
                **render_kwargs
            )
        else:
            bmp = BitmapRenderer.render(
                xs, ys, colors, res, res, xlim, ylim,
                glow=True, use_gpu=gpu, adaptive_eq=adaptive,
                **render_kwargs
            )

        if vib != 1.0:
            bmp = BitmapRenderer.enhance_vibrancy(bmp, vib)

        return bmp

    # ----------------------------------------------------------- generate
    def _generate(self):
        cfg = self._get_cfg()
        iters = self.sl_pts.value()
        seed = self.sp_seed.value() if self.sp_seed.value() >= 0 else None

        self._stop_anim()
        self.btn_gen.setEnabled(False)
        self.btn_anim.setEnabled(False)
        self.prog.setVisible(True)
        self.prog.setValue(0)

        logger.info(
            f"UI -> Generate triggered ({iters:,} points, seed={seed})"
        )

        self._worker = GenerationWorker(cfg, iters, seed)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_err)
        self._worker.start()

        self._prog_val = 0
        self._prog_timer = QTimer()
        self._prog_timer.timeout.connect(self._tick)
        self._prog_timer.start(35)

    def _tick(self):
        self._prog_val = min(self._prog_val + 1, 93)
        self.prog.setValue(self._prog_val)

    def _on_done(self, xs, ys, colors, elapsed, verts):
        self._prog_timer.stop()
        self.prog.setValue(100)
        QTimer.singleShot(350, self.prog.hide)

        self.data = (xs, ys, colors)
        self.verts = verts
        self.cfg = self._get_cfg()
        vis_cfg = self._get_visual_cfg()
        cfg = self.cfg
        res = self._get_resolution()

        # Auto-fit bounds
        self._xlim, self._ylim = BitmapRenderer.compute_bounds(xs, ys)
        self.canvas.set_extent(self._xlim, self._ylim)

        # Choose scatter vs bitmap
        if len(xs) <= SCATTER_THRESHOLD:
            self.canvas.plot_scatter(
                xs, ys, colors, cfg["colormap"],
                cfg["point_size"], self._make_title(cfg, res)
            )
        else:
            bmp = self._render_fractal_bitmap(
                xs, ys, colors, cfg, vis_cfg, res
            )
            self.canvas.show_bitmap(bmp, self._make_title(cfg, res))

        self.btn_gen.setEnabled(True)
        self.btn_anim.setEnabled(True)
        self.statusBar().showMessage(
            f"{len(xs):,} pts in {elapsed:.2f}s  |  {res}×{res}px  |  v={cfg['vertices']}"
        )

    def _on_err(self, msg):
        self._prog_timer.stop()
        self.prog.hide()
        self.btn_gen.setEnabled(True)
        self.btn_anim.setEnabled(True)
        logger.error(f"Generation failed: {msg}")
        self.statusBar().showMessage(f"Error: {msg}", 5000)

    # ----------------------------------------------------------- animation
    def _start_anim(self):
        if not self.data:
            self.statusBar().showMessage("Generate a fractal first!", 3000)
            return

        logger.info("UI -> Animation started")
        xs, ys, colors = self.data
        total = len(xs)
        cfg = self.cfg
        vis_cfg = self._get_visual_cfg()
        w, h = ANIM_RES, ANIM_RES

        self._anim_end = 0
        self._anim_batch = max(3000, total // 100)

        px_all = (
            (xs - self._xlim[0]) / (self._xlim[1] - self._xlim[0]) * (w - 1)
        ).astype(np.int32)
        py_all = (
            1.0 - (ys - self._ylim[0]) / (self._ylim[1] - self._ylim[0]) * (h - 1)
        ).astype(np.int32)
        self._anim_mask = (
            (px_all >= 0) & (px_all < w) & (py_all >= 0) & (py_all < h)
        )
        self._anim_px = px_all[self._anim_mask]
        self._anim_py = py_all[self._anim_mask]
        self._anim_colors = colors[self._anim_mask]
        self._anim_cumsum = np.cumsum(self._anim_mask)

        c_max = max(int(colors.max()), 1)
        self._anim_lut = BitmapRenderer.build_lut(
            cfg["colormap"], c_max,
            vis_cfg["brightness_boost"], vis_cfg["gamma"], vis_cfg["invert"]
        )
        self._anim_img = np.full((h, w, 3), BG_RGB, dtype=np.uint8)

        self.canvas.set_extent(self._xlim, self._ylim)
        self.canvas.init_animation(self._anim_img, f"0 / {total:,}")

        self.btn_anim.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_gen.setEnabled(False)

        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(33)

    def _anim_tick(self):
        xs, ys, colors = self.data
        total = len(xs)
        start_orig = self._anim_end
        end_orig = min(self._anim_end + self._anim_batch, total)

        start_filt = (
            int(self._anim_cumsum[start_orig - 1]) if start_orig > 0 else 0
        )
        end_filt = int(self._anim_cumsum[end_orig - 1])

        if end_filt > start_filt:
            self._anim_img[
                self._anim_py[start_filt:end_filt],
                self._anim_px[start_filt:end_filt]
            ] = self._anim_lut[self._anim_colors[start_filt:end_filt]]

        self._anim_end = end_orig
        self.canvas._img_artist.set_data(self._anim_img)
        self.canvas._add_title_overlay(f"{end_orig:,} / {total:,}")
        self.canvas.draw_idle()

        if end_orig >= total:
            self._stop_anim()
            bmp = self._render_fractal_bitmap(
                xs, ys, colors, self.cfg,
                self._get_visual_cfg()
            )
            self.canvas.show_bitmap(bmp, self._make_title(self.cfg))
            logger.info("UI -> Animation finished")

    def _stop_anim(self):
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None

        for attr in ('_anim_img', '_anim_lut', '_anim_px', '_anim_py',
                      '_anim_mask', '_anim_colors', '_anim_cumsum'):
            if hasattr(self, attr):
                delattr(self, attr)

        self._anim_end = 0
        self.btn_anim.setEnabled(self.data is not None)
        self.btn_stop.setEnabled(False)
        self.btn_gen.setEnabled(True)

    # ----------------------------------------------------------- export
    def _save_png(self):
        if not self.data:
            self.statusBar().showMessage(
                "No data to save. Generate first.", 3000
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save PNG", "fractal.png", "PNG (*.png)"
        )
        if not path:
            return

        logger.info(f"UI -> Saving PNG to {path}")
        self.statusBar().showMessage("Rendering export...", 3000)
        QApplication.processEvents()

        xs, ys, colors = self.data
        bmp = self._render_fractal_bitmap(
            xs, ys, colors, self.cfg,
            self._get_visual_cfg(), EXPORT_RES
        )
        h, w, _ = bmp.shape
        QImage(bmp.data, w, h, 3 * w, QImage.Format_RGB888).copy().save(
            path, quality=95
        )
        size_mb = os.path.getsize(path) / (1024*1024)
        logger.info(f"UI -> PNG saved ({size_mb:.1f} MB)")
        self.statusBar().showMessage(f"Saved: {path} ({size_mb:.1f} MB)", 4000)

    def _save_gif(self):
        if not self.data:
            self.statusBar().showMessage(
                "No data to save. Generate first.", 3000
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "fractal.gif", "GIF (*.gif)"
        )
        if not path:
            return

        self.btn_gif.setEnabled(False)
        self.prog.setVisible(True)
        self.prog.setValue(0)

        xs, ys, colors = self.data
        self._gif_worker = GifWorker(
            xs, ys, colors, self._xlim, self._ylim, self.cfg, path
        )
        self._gif_worker.finished.connect(self._on_gif_done)
        self._gif_worker.error.connect(self._on_gif_err)
        self._gif_worker.progress.connect(self.prog.setValue)
        self._gif_worker.start()

    def _on_gif_done(self, path):
        self.prog.hide()
        self.btn_gif.setEnabled(True)
        self.statusBar().showMessage(f"GIF saved: {path}", 4000)

    def _on_gif_err(self, msg):
        self.prog.hide()
        self.btn_gif.setEnabled(True)
        logger.error(f"GIF export failed: {msg}")
        self.statusBar().showMessage(f"GIF Error: {msg}", 5000)

    # ----------------------------------------------------------- vertices
    def _show_verts(self):
        if not self.verts:
            self.statusBar().showMessage(
                "No vertices to show. Generate first.", 3000
            )
            return
        self.canvas.plot_vertices(self.verts)

    # ----------------------------------------------------------- clear
    def _clear(self):
        self._stop_anim()
        self.data = None
        self.verts = None
        self.cfg = None
        self.canvas.clear_plot()
        self.gallery.clear_selection()
        logger.info("UI -> Canvas cleared")

    # ----------------------------------------------------------- close
    def closeEvent(self, event):
        self._stop_anim()
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        if self._gif_worker and self._gif_worker.isRunning():
            self._gif_worker.terminate()
        event.accept()


# =================================================================== main
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)-8s] %(levelname)-5s  %(message)s",
        datefmt="%H:%M:%S",
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = ChaosGameMainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()