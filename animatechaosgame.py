import matplotlib.pyplot as plt
import numpy as np
import random
import math
from matplotlib.animation import FuncAnimation

# ---- Polygon Vertex Generators ----
def polygon_vertices(n, radius=1.0, center=(0,0), start_angle=math.pi/2):
    cx, cy = center
    return [(cx + radius*math.cos(start_angle + 2*math.pi*k/n),
             cy + radius*math.sin(start_angle + 2*math.pi*k/n))
            for k in range(n)]

def random_polygon_vertices(n, radius=1.0):
    angles = np.sort(np.random.rand(n) * 2 * math.pi)
    return [(math.cos(t) * radius, math.sin(t) * radius) for t in angles]

# ---- Chaos Game Generator (vectorized) ----
def chaos_game_generator(vertices_coords, r=0.5, no_repeat=False, skip=0, total_points=2_000_000):
    vx = np.array([v[0] for v in vertices_coords])
    vy = np.array([v[1] for v in vertices_coords])
    x, y = random.choice(vertices_coords)
    prev_idx = None

    xs = np.zeros(total_points, dtype=np.float32)
    ys = np.zeros(total_points, dtype=np.float32)
    colors = np.linspace(0, 1, total_points, dtype=np.float32)  # gradient

    for i in range(total_points):
        idx = random.randrange(len(vertices_coords))
        if skip > 0 and prev_idx is not None:
            while abs(idx - prev_idx) % len(vertices_coords) <= skip:
                idx = random.randrange(len(vertices_coords))
        if no_repeat and prev_idx is not None:
            while idx == prev_idx:
                idx = random.randrange(len(vertices_coords))
        x += r * (vx[idx] - x)
        y += r * (vy[idx] - y)
        xs[i] = x
        ys[i] = y
        prev_idx = idx

    return xs, ys, colors

# ---- Optimized Animated Gallery ----
def optimized_fractal_gallery(fractal_configs, points_per_fractal=2_000_000, batch_size=50_000):
    fig, ax = plt.subplots(figsize=(6,6), dpi=150)
    ax.axis("equal")
    ax.axis("off")

    current_fractal = 0
    cfg = fractal_configs[current_fractal]
    verts = (polygon_vertices(cfg["vertices"]) 
             if not cfg.get("random_vertices", False) 
             else random_polygon_vertices(cfg["vertices"]))
    
    xs, ys, colors = chaos_game_generator(
        verts,
        r=cfg.get("r", 0.5),
        no_repeat=cfg.get("no_repeat", False),
        skip=cfg.get("skip",0),
        total_points=points_per_fractal
    )

    # Preallocate offsets array
    offsets = np.column_stack((xs, ys))
    scatter = ax.scatter(offsets[:batch_size], offsets[:batch_size], s=0.5,
                         c=colors[:batch_size], cmap=cfg.get("colormap","viridis"), marker=",")
    ax.set_title(cfg.get("title", f"Fractal {current_fractal+1}"))

    total_batches = points_per_fractal // batch_size
    batch_idx = 0

    def update(frame):
        nonlocal batch_idx, current_fractal, xs, ys, colors, scatter, offsets

        start = batch_idx * batch_size
        end = min(start + batch_size, len(xs))
        scatter.set_offsets(offsets[:end])
        scatter.set_array(colors[:end])
        batch_idx += 1

        if batch_idx >= total_batches:
            # Switch to next fractal
            current_fractal = (current_fractal + 1) % len(fractal_configs)
            cfg = fractal_configs[current_fractal]
            verts = (polygon_vertices(cfg["vertices"]) 
                     if not cfg.get("random_vertices", False) 
                     else random_polygon_vertices(cfg["vertices"]))
            xs, ys, colors = chaos_game_generator(
                verts,
                r=cfg.get("r", 0.5),
                no_repeat=cfg.get("no_repeat", False),
                skip=cfg.get("skip",0),
                total_points=points_per_fractal
            )
            offsets = np.column_stack((xs, ys))
            scatter.set_cmap(cfg.get("colormap","viridis"))
            ax.set_title(cfg.get("title", f"Fractal {current_fractal+1}"))
            batch_idx = 0

        return scatter,

    anim = FuncAnimation(fig, update,
                         frames=total_batches * len(fractal_configs),
                         interval=50, blit=False)
    plt.show()

# ---- Example Fractals ----
fractal_configs = [
    {"vertices": 3, "r": 0.5, "title":"Sierpinski Triangle", "colormap":"viridis"},
    {"vertices": 5, "r": 0.618, "title":"Pentagon Golden Ratio", "colormap":"cividis"},
    {"vertices": 5, "r": 0.618, "skip":1, "title":"Pentagram Chaos Game", "colormap":"cool"},
    {"vertices": 7, "r": 0.5, "random_vertices":True, "title":"Random Heptagon", "colormap":"plasma"},
]

optimized_fractal_gallery(fractal_configs)
