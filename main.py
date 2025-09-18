import matplotlib.pyplot as plt
import numpy as np
import random
import math

def polygon_vertices(n, radius=1.0, center=(0, 0), start_angle=math.pi / 2):
    cx, cy = center
    return [
        (cx + radius * math.cos(start_angle + 2 * math.pi * k / n),
         cy + radius * math.sin(start_angle + 2 * math.pi * k / n))
        for k in range(n)
    ]

def chaos_game(vertices=3, r=0.5, iterations=200000, burn_in=50,
               no_repeat=False, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    verts = polygon_vertices(vertices)
    vx = np.array([v[0] for v in verts])
    vy = np.array([v[1] for v in verts])

    xs, ys, colors = [], [], []
    x, y = random.uniform(-1, 1), random.uniform(-1, 1)
    prev_idx = None

    for i in range(iterations + burn_in):
        idx = random.randrange(vertices)
        if no_repeat and prev_idx is not None:
            while idx == prev_idx:
                idx = random.randrange(vertices)

        x = x + r * (vx[idx] - x)
        y = y + r * (vy[idx] - y)
        prev_idx = idx

        if i >= burn_in:
            xs.append(x)
            ys.append(y)
            colors.append(idx)  # color based on vertex

    return np.array(xs), np.array(ys), verts, np.array(colors)

def plot_fractal(vertices=3, r=0.5, iterations=200000,
                 burn_in=50, no_repeat=False, seed=None, title=None,
                 colormap="tab10"):
    xs, ys, verts, colors = chaos_game(vertices, r, iterations,
                                       burn_in=burn_in,
                                       no_repeat=no_repeat, seed=seed)

    plt.figure(figsize=(6, 6), dpi=150)
    plt.scatter(xs, ys, c=colors, cmap=colormap, s=0.1, marker=",")
    plt.axis("equal")
    plt.axis("off")
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_fractal(vertices=3, r=0.5, iterations=100000, title="Sierpinski Triangle", colormap="viridis")
    plot_fractal(vertices=4, r=0.5, iterations=150000, no_repeat=True, title="Square Chaos Game", colormap="plasma")
    plot_fractal(vertices=5, r=0.618, iterations=200000, title="Pentagon Golden Ratio", colormap="cividis")
    plot_fractal(vertices=6, r=0.333, iterations=200000, title="Hexagon Variant", colormap="tab10")
