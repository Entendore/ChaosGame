"""
Chaos Game Fractal Generator — Background Workers
"""

import time
import logging
import numpy as np
from PySide6.QtCore import QThread, Signal
from chaos_engine import ChaosGame

logger = logging.getLogger("Worker")


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
            logger.info(f"Generation SUCCESS in {elapsed:.3f}s")
            self.finished.emit(xs, ys, colors, elapsed, g.verts)
        except Exception as e:
            logger.error(f"Generation FAILED: {str(e)}")
            self.error.emit(str(e))


class GifWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, xs, ys, colors, xlim, ylim, cfg, path, n_frames=60):
        super().__init__()
        self.xs, self.ys, self.colors = xs, ys, colors
        self.xlim, self.ylim = xlim, ylim
        self.cfg = cfg
        self.path = path
        self.n_frames = n_frames

    def run(self):
        try:
            logger.info(f"Starting GIF export to {self.path}...")
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.animation

            from config import C, BG_RGB
            from renderer import BitmapRenderer

            xs, ys, colors = self.xs, self.ys, self.colors
            total = len(xs)
            gw, gh = 800, 800
            n_frames = self.n_frames
            batch = max(1, total // n_frames)

            fig, ax = plt.subplots(figsize=(6, 6), dpi=80, facecolor=C["canvas_bg"])
            ax.set_facecolor(C["canvas_bg"])
            ax.axis("off")
            ax.set_aspect("equal")
            fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.01)

            blank = np.full((gh, gw, 3), BG_RGB, dtype=np.uint8)
            extent = list(self.xlim) + list(self.ylim)
            im = ax.imshow(blank, aspect="equal", interpolation="bilinear",
                           extent=extent, origin="upper")
            info = ax.text(0.5, 0.98, "", ha="center", va="top",
                           transform=fig.transFigure, fontsize=9,
                           color=C["text"], fontweight="bold",
                           fontfamily="monospace")

            def update(frame):
                end = min((frame + 1) * batch, total)
                bmp = BitmapRenderer.render_direct(
                    xs[:end], ys[:end], colors[:end],
                    gw, gh, self.xlim, self.ylim, self.cfg["colormap"]
                )
                im.set_data(bmp)
                info.set_text(f"{end:,} / {total:,}")
                self.progress.emit(int((frame + 1) / n_frames * 100))
                return [im, info]

            anim = matplotlib.animation.FuncAnimation(
                fig, update, frames=n_frames, interval=50, blit=True
            )
            writer = matplotlib.animation.PillowWriter(fps=20)
            anim.save(self.path, writer=writer)
            plt.close(fig)
            logger.info("GIF export SUCCESS")
            self.finished.emit(self.path)

        except Exception as e:
            logger.error(f"GIF export FAILED: {str(e)}")
            self.error.emit(str(e))