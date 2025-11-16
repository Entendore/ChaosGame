import matplotlib.pyplot as plt
import numpy as np
import random
import math

# ---- Polygon Vertex Generators ----
def polygon_vertices(n, radius=1.0, center=(0,0), start_angle=math.pi/2):
    cx, cy = center
    return [(cx + radius*math.cos(start_angle + 2*math.pi*k/n),
             cy + radius*math.sin(start_angle + 2*math.pi*k/n))
            for k in range(n)]

def random_polygon_vertices(n, radius=1.0):
    angles = np.sort(np.random.rand(n)*2*math.pi)
    return [(math.cos(t)*radius, math.sin(t)*radius) for t in angles]

# ---- Chaos Game Core ----
def chaos_game(vertices_coords, r=0.5, iterations=200000, burn_in=50, no_repeat=False):
    vx = np.array([v[0] for v in vertices_coords])
    vy = np.array([v[1] for v in vertices_coords])
    xs, ys, colors = [], [], []
    x, y = random.uniform(-1,1), random.uniform(-1,1)
    prev_idx = None

    for i in range(iterations + burn_in):
        idx = random.randrange(len(vertices_coords))
        if no_repeat and prev_idx is not None:
            while idx == prev_idx:
                idx = random.randrange(len(vertices_coords))
        x = x + r * (vx[idx] - x)
        y = y + r * (vy[idx] - y)
        prev_idx = idx
        if i >= burn_in:
            xs.append(x)
            ys.append(y)
            colors.append(idx)
    return np.array(xs), np.array(ys), np.array(colors)

# ---- Plot Function ----
def plot_fractal(xs, ys, colors, title=None, colormap="tab10"):
    plt.figure(figsize=(6,6), dpi=150)
    plt.scatter(xs, ys, c=colors, cmap=colormap, s=0.1, marker=",")
    plt.axis("equal")
    plt.axis("off")
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.show()

# ---- Gallery Configurations ----
fractal_configs = [
    {"vertices": 3, "r": 0.5, "title":"Sierpinski Triangle", "colormap":"viridis"},
    {"vertices": 4, "r": 0.5, "no_repeat":True, "title":"Square Chaos Game", "colormap":"plasma"},
    {"vertices": 5, "r": 0.618, "title":"Pentagon Golden Ratio", "colormap":"cividis"},
    {"vertices": 6, "r": 1/3, "title":"Hexagon Variant", "colormap":"tab10"},
    {"vertices": 3, "r": None, "title":"Triangle Random r", "colormap":"magma"},
    {"vertices": 5, "r": 0.618, "skip":1, "title":"Pentagram Chaos Game", "colormap":"cool"},
    {"vertices": 7, "r": 0.5, "random_vertices":True, "title":"Random Heptagon", "colormap":"plasma"},
    {"vertices": 8, "r": 0.618, "title":"Octagon Golden Ratio", "colormap":"cividis"},
    {"vertices": 10, "r": 0.7, "title":"Decagon Chaos", "colormap":"magma"},
    {"vertices": 12, "r": 0.5, "title":"Dodecagon Fractal", "colormap":"tab20"}
]

# ---- Generate Gallery ----
for cfg in fractal_configs:
    vertices = cfg.get("vertices")
    r = cfg.get("r", 0.5)
    title = cfg.get("title")
    colormap = cfg.get("colormap", "tab10")
    no_repeat = cfg.get("no_repeat", False)
    skip = cfg.get("skip", 0)
    random_vertices = cfg.get("random_vertices", False)

    if random_vertices:
        verts = random_polygon_vertices(vertices)
    else:
        verts = polygon_vertices(vertices)

    # Special case: random r for each step
    if r is None:
        xs, ys, colors = [], [], []
        x, y = random.uniform(-1,1), random.uniform(-1,1)
        for i in range(200000):
            idx = random.randrange(vertices)
            r_step = random.uniform(0.3,0.7)
            x = x + r_step*(verts[idx][0]-x)
            y = y + r_step*(verts[idx][1]-y)
            xs.append(x)
            ys.append(y)
            colors.append(idx)
        xs, ys, colors = np.array(xs), np.array(ys), np.array(colors)
    # Special case: skip vertices (Pentagram style)
    elif skip > 0:
        xs, ys, colors = [], [], []
        x, y = random.uniform(-1,1), random.uniform(-1,1)
        prev_idx = None
        for i in range(200000):
            idx = random.randrange(vertices)
            while prev_idx is not None and abs(idx - prev_idx) % vertices <= skip:
                idx = random.randrange(vertices)
            x = x + r*(verts[idx][0]-x)
            y = y + r*(verts[idx][1]-y)
            prev_idx = idx
            xs.append(x)
            ys.append(y)
            colors.append(idx)
        xs, ys, colors = np.array(xs), np.array(ys), np.array(colors)
    else:
        xs, ys, colors = chaos_game(verts, r=r, iterations=200000, no_repeat=no_repeat)

    plot_fractal(xs, ys, colors, title=title, colormap=colormap)
