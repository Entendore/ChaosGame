"""
Chaos Game Fractal Generator — Matplotlib Canvas
Interactive smooth zoom and pan without the ugly toolbar.
"""

import numpy as np
from typing import List, Tuple

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import C


class FractalCanvas(FigureCanvas):

    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=C["canvas_bg"])
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._extent = [-1.5, 1.5, -1.5, 1.5]
        self._img_artist = None
        self._title_text = None
        self._setup()

        self.mpl_connect('scroll_event', self._on_scroll)
        self.mpl_connect('button_press_event', self._on_click)

    def _setup(self):
        ax = self.ax
        ax.set_facecolor(C["canvas_bg"])
        ax.set_xlim(self._extent[0], self._extent[1])
        ax.set_ylim(self._extent[2], self._extent[3])
        ax.set_aspect("equal")
        ax.axis("off")
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.02)

    def _clear_overlay(self):
        if self._title_text is not None:
            try:
                self._title_text.remove()
            except ValueError:
                pass
            self._title_text = None

    def _add_title_overlay(self, title: str = ""):
        if self._title_text is None:
            self._title_text = self.fig.text(
                0.5, 0.97, title, ha="center", va="top",
                fontsize=12, color=C["text"], fontweight="bold",
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=C["bg0"],
                          alpha=0.75, edgecolor=C["border"], linewidth=1)
            )
        else:
            self._title_text.set_text(title)

    def set_extent(self, xlim, ylim):
        self._extent = [xlim[0], xlim[1], ylim[0], ylim[1]]

    def clear_plot(self):
        self._extent = [-1.5, 1.5, -1.5, 1.5]
        self._clear_overlay()
        self.ax.clear()
        self._setup()
        self._img_artist = None
        self.draw_idle()

    def show_bitmap(self, bitmap: np.ndarray, title: str = ""):
        self._clear_overlay()
        self.ax.clear()
        self._setup()
        self._img_artist = self.ax.imshow(
            bitmap, aspect="equal", interpolation="bilinear",
            extent=self._extent, origin="upper"
        )
        self._add_title_overlay(title)
        self.draw_idle()

    def update_bitmap(self, bitmap: np.ndarray, title: str = ""):
        if self._img_artist is not None:
            self._img_artist.set_data(bitmap)
            if title:
                self._add_title_overlay(title)
            self.draw_idle()

    def plot_scatter(self, xs, ys, colors, cmap_name="viridis",
                     point_size=0.1, title=""):
        self._clear_overlay()
        self.ax.clear()
        self._setup()
        self._img_artist = None
        vmin, vmax = int(colors.min()), int(colors.max())
        if vmin == vmax:
            vmax = vmin + 1
        self.ax.scatter(
            xs, ys, c=colors, cmap=cmap_name, s=point_size,
            marker=".", alpha=0.9, linewidths=0,
            vmin=vmin, vmax=vmax, rasterized=True
        )
        self._add_title_overlay(title)
        self.draw_idle()

    def plot_vertices(self, verts: List[Tuple[float, float]]):
        vx = [v[0] for v in verts]
        vy = [v[1] for v in verts]
        self.ax.plot(vx + [vx[0]], vy + [vy[0]], "-",
                     color=C["accent"], linewidth=3.0, alpha=0.3, zorder=9)
        self.ax.plot(vx + [vx[0]], vy + [vy[0]], "o-",
                     color=C["accent"], markersize=8, linewidth=1.5,
                     alpha=0.9, zorder=10)
        for i, (x, y) in enumerate(verts):
            self.ax.annotate(
                str(i), (x, y), textcoords="offset points", xytext=(8, 8),
                fontsize=9, color="#ffffff", fontweight="bold", zorder=11,
                bbox=dict(boxstyle="round,pad=0.2", fc=C["bg0"],
                          alpha=0.7, ec="none")
            )
        self.draw_idle()

    def init_animation(self, blank_img: np.ndarray, title: str = ""):
        self._clear_overlay()
        self.ax.clear()
        self._setup()
        self._img_artist = self.ax.imshow(
            blank_img, aspect="equal", interpolation="bilinear",
            extent=self._extent, origin="upper"
        )
        self._add_title_overlay(title)
        self.draw()

    # --- Modern Interactions (Replaces Toolbar) ---

    def _on_scroll(self, event):
        """Smooth zoom exactly where the mouse cursor is pointing."""
        if event.inaxes != self.ax or self._img_artist is None:
            return

        scale_factor = 1.15
        if event.button == 'up':
            scale_factor = 1 / scale_factor
        elif event.button == 'down':
            pass

        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
        xdata, ydata = event.xdata, event.ydata

        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor

        relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
        rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx),
                          xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely),
                          ydata + new_height * rely])
        self.draw_idle()

    def _on_click(self, event):
        """Double-click to instantly reset the view."""
        if event.dblclick and event.inaxes == self.ax:
            self.ax.set_xlim(self._extent[0], self._extent[1])
            self.ax.set_ylim(self._extent[2], self._extent[3])
            self.draw_idle()