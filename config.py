"""
Chaos Game Fractal Generator — Configuration
Enhanced with resolution presets, more palettes, and visibility controls
"""

import math
import matplotlib.colors as mcolors

# ============================================================
# Color Palette — "Midnight Observatory"
# ============================================================
C = {
    "bg0":        "#080c14",
    "bg1":        "#0d1220",
    "bg2":        "#131a2b",
    "bg3":        "#1a2438",
    "bg4":        "#222e44",
    "border":     "#1c2a3e",
    "accent":     "#14b8a6",
    "accent2":    "#0d9488",
    "accent_dim": "#0a6b63",
    "text":       "#e2e8f0",
    "text2":      "#94a3b8",
    "text3":      "#475569",
    "rose":       "#f43f5e",
    "canvas_bg":  "#080c14",
}

BG_RGB = (8, 12, 20)

# ============================================================
# Resolution Presets
# ============================================================
RESOLUTION_PRESETS = {
    "512 × 512":     512,
    "768 × 768":     768,
    "1024 × 1024":   1024,
    "1280 × 1280":   1280,
    "1536 × 1536":   1536,
    "2048 × 2048":   2048,
    "3072 × 3072":   3072,
    "4096 × 4096":   4096,
}

DEFAULT_DISPLAY_RES = 1024
EXPORT_RES = 4096
ANIM_RES = 768
SCATTER_THRESHOLD = 30_000

# Points per million pixels - higher for better density
POINTS_DENSITY = {
    512:   80_000,
    768:   150_000,
    1024:  250_000,
    1280:  400_000,
    1536:  550_000,
    2048:  800_000,
    3072:  1_500_000,
    4096:  2_000_000,
}

# ============================================================
# Enhanced Custom Vibrant Palettes
# ============================================================
_CUSTOM_CMAPS = {
    # Neon family
    "neon":           ['#0d1b2a', '#00ffff', '#ffffff', '#ff00ff', '#0d1b2a'],
    "neon_green":     ['#050d05', '#003300', '#00ff00', '#aaffaa', '#ffffff'],
    "neon_pink":      ['#1a0515', '#330033', '#ff00ff', '#ff66cc', '#ffffff'],
    "neon_blue":      ['#050510', '#000066', '#0066ff', '#66ccff', '#ffffff'],
    
    # Cyberpunk family
    "cyberpunk":      ['#1a0a2a', '#0f084b', '#26408b', '#a6f0c6', '#f72585'],
    "synthwave":      ['#0a001a', '#1a0033', '#6600cc', '#ff0066', '#ffcc00'],
    "retrowave":      ['#0d001a', '#330066', '#cc00ff', '#ff3399', '#ff9966'],
    "vaporwave":      ['#1a0a2e', '#ff71ce', '#01cdfe', '#05ffa1', '#b967ff'],
    
    # Nature family
    "toxic":          ['#0a1a0a', '#004d00', '#00ff00', '#ccff00', '#ffffff'],
    "lava":           ['#1a0505', '#8b0000', '#ff4500', '#ffd700', '#ffffe0'],
    "forest":         ['#0a150a', '#1a4d1a', '#2d8b2d', '#66cc66', '#ccffcc'],
    "ocean":          ['#050515', '#000066', '#0099ff', '#00ffcc', '#ffffff'],
    "sunset":         ['#1a0a05', '#8b4513', '#ff6347', '#ffa500', '#ffff99'],
    "aurora":         ['#050515', '#003366', '#00cc99', '#66ff66', '#cc66ff'],
    
    # Electric family
    "electric":       ['#05051a', '#0000ff', '#00ffff', '#ffffff', '#ff00ff'],
    "plasma_wave":    ['#0a0020', '#3300aa', '#ff00ff', '#ff6600', '#ffff00'],
    "lightning":      ['#050510', '#333399', '#6666ff', '#ffffff', '#ffff66'],
    
    # Candy/Pastel family
    "candy":          ['#1a0515', '#ff00ff', '#ff6699', '#ffcc00', '#ffffff'],
    "pastel_dream":   ['#1a1a2e', '#ffadad', '#ffd6a5', '#caffbf', '#bdb2ff'],
    "cotton_candy":   ['#1a0a1a', '#ff99cc', '#cc99ff', '#99ccff', '#ffffff'],
    
    # Dark/Moody
    "midnight":       ['#000000', '#0d0d2b', '#1a1a4d', '#333399', '#6666cc'],
    "deep_space":     ['#000000', '#0a0a1a', '#1a1a3a', '#333366', '#6666aa'],
    "blood_moon":     ['#0a0000', '#330000', '#990000', '#cc3300', '#ff6633'],
    
    # High Contrast
    "high_contrast":  ['#000000', '#ff0000', '#00ff00', '#0000ff', '#ffffff'],
    "thermal":        ['#000000', '#0000ff', '#00ffff', '#ffff00', '#ff0000'],
    "xray":           ['#000000', '#1a1a1a', '#666666', '#cccccc', '#ffffff'],
}

# ============================================================
# Colormaps
# ============================================================
COLORMAPS = [
    # Custom palettes first (sorted by category)
    "-- Neon --",
    "Neon", "Neon Green", "Neon Pink", "Neon Blue",
    "-- Cyberpunk --",
    "Cyberpunk", "Synthwave", "Retrowave", "Vaporwave",
    "-- Nature --",
    "Toxic", "Lava", "Forest", "Ocean", "Sunset", "Aurora",
    "-- Electric --",
    "Electric", "Plasma Wave", "Lightning",
    "-- Candy --",
    "Candy", "Pastel Dream", "Cotton Candy",
    "-- Dark/Moody --",
    "Midnight", "Deep Space", "Blood Moon",
    "-- High Contrast --",
    "High Contrast", "Thermal", "Xray",
    "-- Matplotlib --",
    "turbo", "rainbow", "nipy_spectral", "Spectral", "gist_stern",
    "plasma", "inferno", "magma", "hot",
    "twilight", "twilight_shifted", "cubehelix", "cividis",
    "tab10", "tab20", "Set1", "Set2", "Set3", "Paired", "Dark2",
    "viridis", "cool", "warm", "gist_earth", "RdYlBu", "RdPu",
    "BuGn", "PuBu", "YlOrBr", "YlOrRd", "spring", "summer",
    "autumn", "winter", "bone", "pink", "gray", "Accent", "Pastel1",
]


def get_cmap(name: str):
    import matplotlib
    # Skip separator items
    if name.startswith("--"):
        return None
    name_lower = name.lower().replace(" ", "_")
    
    if name_lower in _CUSTOM_CMAPS:
        return mcolors.LinearSegmentedColormap.from_list(
            name, _CUSTOM_CMAPS[name_lower], N=512  # Higher N for smoother gradients
        )
    try:
        return matplotlib.colormaps[name]
    except (AttributeError, KeyError):
        import matplotlib.cm as cm
        return cm.get_cmap(name)


# ============================================================
# Presets — tuned for 1024x1024 by default
# ============================================================
PRESETS = [
    {"vertices": 3,  "r": 0.5,   "title": "Sierpinski Triangle",
     "colormap": "Neon",              "point_size": 10, "resolution": 1024},
    {"vertices": 3,  "r": None,   "title": "Triangle · Random r",
     "colormap": "Lava",              "point_size": 10, "resolution": 1024},
    {"vertices": 4,  "r": 0.5,   "no_repeat": True,
     "title": "Square No-Repeat",   "colormap": "Candy",         "point_size": 10, "resolution": 1024},
    {"vertices": 4,  "r": 0.5,   "skip": 1,
     "title": "Square Maze",        "colormap": "Cyberpunk",     "point_size": 8, "resolution": 1024},
    {"vertices": 5,  "r": 0.618, "title": "Golden Pentagon",
     "colormap": "Electric",          "point_size": 10, "resolution": 1024},
    {"vertices": 5,  "r": 0.618, "skip": 1,
     "title": "Pentagram Void",     "colormap": "Toxic",         "point_size": 10, "resolution": 1024},
    {"vertices": 6,  "r": 0.5,   "title": "Hexagonal Snowflake",
     "colormap": "Ocean",             "point_size": 8, "resolution": 1024},
    {"vertices": 6,  "r": 1/3,   "title": "Hexagon r = ⅓",
     "colormap": "Aurora",            "point_size": 10, "resolution": 1024},
    {"vertices": 6,  "r": 0.5,   "skip": 2,
     "title": "Star of David",      "colormap": "Synthwave",     "point_size": 15, "resolution": 1024},
    {"vertices": 7,  "r": 0.5,   "random_vertices": True,
     "title": "Chaotic Heptagon",   "colormap": "Plasma Wave",   "point_size": 10, "resolution": 1024},
    {"vertices": 8,  "r": 0.5,   "title": "Octagonal Vortex",
     "colormap": "Vaporwave",        "point_size": 6, "resolution": 1024},
    {"vertices": 8,  "r": 0.618, "title": "Octagon Golden",
     "colormap": "cividis",           "point_size": 8, "resolution": 1024},
    {"vertices": 9,  "r": 0.45,  "skip": 1,
     "title": "Nonagonal Nebula",   "colormap": "Spectral",      "point_size": 6, "resolution": 1024},
    {"vertices": 10, "r": 0.7,   "title": "Decagon Chaos",
     "colormap": "Rainbow",           "point_size": 6, "resolution": 1024},
    {"vertices": 10, "r": 0.5,   "title": "Decagonal Bloom",
     "colormap": "Twilight Shifted",  "point_size": 6, "resolution": 1024},
    {"vertices": 12, "r": 0.5,   "title": "Dodecagonal Cosmos",
     "colormap": "Pastel Dream",      "point_size": 4, "resolution": 1024},
]