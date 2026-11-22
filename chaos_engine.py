"""
Chaos Game Fractal Generator — Chaos Game Engine
Includes polygon generation and the core game logic.
"""

import math
import numpy as np
import logging
from typing import List, Tuple

from compute_backend import (
    _chaos_standard, _chaos_random_r, _chaos_skip
)

logger = logging.getLogger("Engine")


# ============================================================
# Polygon Generation
# ============================================================
class PolygonGenerator:
    @staticmethod
    def regular(n: int, radius: float = 1.0,
                start_angle: float = math.pi / 2) -> List[Tuple[float, float]]:
        """Generate vertices of a regular n-gon inscribed in a circle."""
        return [
            (radius * math.cos(start_angle + 2 * math.pi * k / n),
             radius * math.sin(start_angle + 2 * math.pi * k / n))
            for k in range(n)
        ]

    @staticmethod
    def random_polygon(n: int, radius: float = 1.0,
                       seed=None) -> List[Tuple[float, float]]:
        """Generate vertices at sorted random angles (convex polygon)."""
        if seed is not None:
            np.random.seed(seed)
        angles = np.sort(np.random.rand(n) * 2 * math.pi)
        return [(math.cos(t) * radius, math.sin(t) * radius) for t in angles]


# ============================================================
# Chaos Game
# ============================================================
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

        # Capped at 2^31-1 to prevent int32 overflow
        self.seed_val = seed if seed is not None else np.random.randint(0, 2**31 - 1)
        np.random.seed(self.seed_val)

        self.verts = (
            PolygonGenerator.random_polygon(vertices, seed=seed)
            if random_vertices
            else PolygonGenerator.regular(vertices)
        )
        self.vx = np.array([v[0] for v in self.verts], dtype=np.float64)
        self.vy = np.array([v[1] for v in self.verts], dtype=np.float64)

        self._skip_tables = None
        self._skip_counts = None
        if skip > 0:
            self._build_skip_tables()

    def _build_skip_tables(self):
        nv = self.vertices
        tables, counts = [], []
        for i in range(nv):
            v = [j for j in range(nv)
                 if min(abs(i - j), nv - abs(i - j)) > self.skip]
            if not v:
                v = list(range(nv))
            tables.append(np.array(v, dtype=np.int64))
            counts.append(np.int64(len(v)))
        max_len = max(len(t) for t in tables)
        self._skip_tables = np.full((nv, max_len), -1, dtype=np.int64)
        self._skip_counts = np.array(counts, dtype=np.int64)
        for i, t in enumerate(tables):
            self._skip_tables[i, :len(t)] = t

    def generate(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mode = ("Random R" if self.r is None
                else ("Skip" if self.skip > 0 else "Standard"))
        logger.info(
            f"Executing {mode} chaos game | Verts: {self.vertices} "
            f"| Iterations: {self.iterations:,} | Seed: {self.seed_val}"
        )

        if self.r is None:
            return _chaos_random_r(
                self.vx, self.vy, self.vertices, self.burn_in, self.iterations
            )
        elif self.skip > 0 and self._skip_tables is not None:
            return _chaos_skip(
                self.vx, self.vy, self.vertices, self.r,
                self.burn_in, self.iterations,
                self._skip_tables, self._skip_counts
            )
        else:
            return _chaos_standard(
                self.vx, self.vy, self.vertices, self.r,
                self.burn_in, self.iterations, self.seed_val
            )