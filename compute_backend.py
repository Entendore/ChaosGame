"""
Chaos Game Fractal Generator — Compute Backend & Bitmap Renderer
Enhanced with better visibility defaults, fixed coordinate mapping, and debugging
"""

import numpy as np
import logging

from config import BG_RGB, get_cmap

logger = logging.getLogger("Backend")

HAS_NUMBA = False
HAS_CUPY = False

try:
    from numba import njit, prange
    HAS_NUMBA = True
    logger.info("Numba JIT acceleration: ENABLED")
except ImportError:
    logger.warning("Numba JIT acceleration: DISABLED (pip install numba)")
    def njit(*args, **kwargs):
        def _dec(func): return func
        if args and callable(args[0]): return args[0]
        return _dec
    def prange(*a, **kw): return range(*a, **kw)

try:
    import cupy as cp
    HAS_CUPY = True
    logger.info("CuPy GPU acceleration: ENABLED")
except ImportError:
    logger.warning("CuPy GPU acceleration: DISABLED (pip install cupy-cuda12x)")
    cp = None


def get_backend_info() -> str:
    return f"Numba: {'✓' if HAS_NUMBA else '✗'}  |  CuPy (GPU): {'✓' if HAS_CUPY else '✗'}"


# ================================================================
#  Numba-accelerated chaos game kernels
# ================================================================
if HAS_NUMBA:
    @njit(cache=True)
    def _chaos_standard(vx, vy, nv, r, burn_in, iterations, seed_val):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, prev, j = 0.0, 0.0, -1, 0
        for i in range(burn_in + iterations):
            idx = int(np.random.random() * nv)
            if idx == prev and nv > 1:
                idx = int(np.random.random() * nv)
                if idx == prev: idx = (prev + 1) % nv
            x += r * (vx[idx] - x); y += r * (vy[idx] - y); prev = idx
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co

    @njit(cache=True)
    def _chaos_random_r(vx, vy, nv, burn_in, iterations):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, j = 0.0, 0.0, 0
        for i in range(burn_in + iterations):
            idx = int(np.random.random() * nv); rs = 0.3 + 0.4 * np.random.random()
            x += rs * (vx[idx] - x); y += rs * (vy[idx] - y)
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co

    @njit(cache=True)
    def _chaos_skip(vx, vy, nv, r, burn_in, iterations, skip_tables, skip_counts):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, prev, j = 0.0, 0.0, 0, 0
        for i in range(burn_in + iterations):
            t = skip_tables[prev]; c = skip_counts[prev]
            idx = int(t[int(np.random.random() * c)])
            x += r * (vx[idx] - x); y += r * (vy[idx] - y); prev = idx
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co
else:
    def _chaos_standard(vx, vy, nv, r, burn_in, iterations, seed_val):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, prev, j = 0.0, 0.0, -1, 0
        for i in range(burn_in + iterations):
            idx = int(np.random.random() * nv)
            if idx == prev and nv > 1:
                idx = int(np.random.random() * nv)
                if idx == prev: idx = (prev + 1) % nv
            x += r * (vx[idx] - x); y += r * (vy[idx] - y); prev = idx
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co

    def _chaos_random_r(vx, vy, nv, burn_in, iterations):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, j = 0.0, 0.0, 0
        for i in range(burn_in + iterations):
            idx = int(np.random.random() * nv); rs = 0.3 + 0.4 * np.random.random()
            x += rs * (vx[idx] - x); y += rs * (vy[idx] - y)
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co

    def _chaos_skip(vx, vy, nv, r, burn_in, iterations, skip_tables, skip_counts):
        xs = np.empty(iterations, np.float32)
        ys = np.empty(iterations, np.float32)
        co = np.empty(iterations, np.int32)
        x, y, prev, j = 0.0, 0.0, 0, 0
        for i in range(burn_in + iterations):
            t = skip_tables[prev]; c = skip_counts[prev]
            idx = int(t[int(np.random.random() * c)])
            x += r * (vx[idx] - x); y += r * (vy[idx] - y); prev = idx
            if i >= burn_in: xs[j] = x; ys[j] = y; co[j] = idx; j += 1
        return xs, ys, co


# ================================================================
#  GPU Renderers (CuPy)
# ================================================================
def render_bincount_gpu(flat, pc, height, width, bg):
    flat_g, pc_g = cp.asarray(flat), cp.asarray(pc)
    n_pix = height * width
    img = cp.zeros((3, n_pix), dtype=cp.float32)
    weights = cp.zeros(n_pix, dtype=cp.float32)
    for ch in range(3):
        img[ch] = cp.bincount(flat_g, weights=pc_g[:, ch], minlength=n_pix)[:n_pix]
    weights = cp.bincount(flat_g, minlength=n_pix)[:n_pix]
    img = img.reshape(3, height, width).transpose(1, 2, 0)
    weights = weights.reshape(height, width)
    nz = weights > 0; img[nz] /= weights[nz, cp.newaxis]
    result = cp.full((height, width, 3), bg, dtype=cp.uint8)
    result[nz] = cp.clip(img[nz], 0, 255).astype(cp.uint8)
    return cp.asnumpy(result)


def render_glow_gpu(img, radius, intensity, bg):
    from cupyx.scipy.ndimage import uniform_filter
    img_g = cp.asarray(img.astype(np.float32))
    blurred = uniform_filter(img_g, size=(2 * radius + 1, 2 * radius + 1, 1))
    bg_f = cp.array(bg, dtype=cp.float32)
    is_bg = cp.all(img_g == bg_f, axis=2)
    out = img_g * (1.0 - intensity) + blurred * intensity
    out[is_bg] = bg_f
    return cp.asnumpy(cp.clip(out, 0, 255).astype(cp.uint8))


# ================================================================
#  Enhanced Bitmap Renderer
# ================================================================
class BitmapRenderer:

    @staticmethod
    def _map_coords(xs, ys, w, h, xlim, ylim):
        """Map fractal coordinates to pixel coordinates."""
        px = ((xs - xlim[0]) / (xlim[1] - xlim[0]) * (w - 1)).astype(np.int32)
        
        # CRITICAL FIX: Parentheses moved so (h - 1) multiplies AFTER the 0.0-1.0 fraction is calculated
        py = ((1.0 - (ys - ylim[0]) / (ylim[1] - ylim[0])) * (h - 1)).astype(np.int32)
        
        mask = (px >= 0) & (px < w) & (py >= 0) & (py < h)
        
        if not np.any(mask):
            logger.error(
                f"Mapped coordinates out of bounds!\n"
                f"  px range: [{px.min()}, {px.max()}] (needs 0-{w-1})\n"
                f"  py range: [{py.min()}, {py.max()}] (needs 0-{h-1})\n"
                f"  xs range: [{xs.min():.3f}, {xs.max():.3f}] | xlim: {xlim}\n"
                f"  ys range: [{ys.min():.3f}, {ys.max():.3f}] | ylim: {ylim}"
            )
            
        return px, py, mask

    @staticmethod
    def build_lut(cmap_name: str, c_max: int, brightness_boost: float = 0.0,
                  gamma: float = 1.0, invert: bool = False) -> np.ndarray:
        """
        Build color lookup table with enhanced visibility controls.
        Samples from 0.15 to 0.85 to AVOID dark endpoints that blend into the background.
        """
        cmap_obj = get_cmap(cmap_name)
        if cmap_obj is None:
            cmap_obj = get_cmap("viridis")
        
        # Sample from 0.15 to 0.85 to avoid dark endpoints entirely
        positions = np.linspace(0.15, 0.85, max(c_max + 1, 2))
        lut = (cmap_obj(positions)[:, :3] * 255).astype(np.float32)
        
        bg_f = np.array(BG_RGB, dtype=np.float32)  # (8, 12, 20)
        
        # Ensure minimum visibility - each channel must be significantly above background
        min_brightness = 80.0 + brightness_boost * 120.0  # 80-200 minimum
        
        for ch in range(3):
            channel_min = max(min_brightness, bg_f[ch] + 60.0)
            lut[:, ch] = np.maximum(lut[:, ch], channel_min)
        
        # Ensure at least one channel is bright (saturation check)
        max_per_row = np.max(lut, axis=1)
        dim_mask = max_per_row < 150.0
        if np.any(dim_mask):
            # Boost dim colors to be more visible
            boost_factor = 150.0 / max_per_row[dim_mask]
            lut[dim_mask] = np.clip(lut[dim_mask] * boost_factor[:, np.newaxis], 0, 255)
        
        # Apply gamma correction (gamma < 1 brightens, > 1 darkens)
        if gamma != 1.0:
            lut = np.power(lut / 255.0, gamma) * 255.0
        
        # Invert palette
        if invert:
            lut = 255.0 - lut
        
        result = np.clip(lut, 0, 255).astype(np.uint8)
        
        logger.debug(f"LUT built: {cmap_name}, c_max={c_max}, samples={result.shape[0]}, "
                    f"min={result.min()}, max={result.max()}")
        
        return result

    @staticmethod
    def adaptive_brightness(img, target_brightness: float = 0.55, bg=BG_RGB):
        """Adaptively adjust brightness based on actual image content."""
        bg_f = np.array(bg, dtype=np.float32)
        is_fg = ~np.all(img.astype(np.float32) == bg_f, axis=2)
        
        if not np.any(is_fg):
            logger.warning("adaptive_brightness: No foreground pixels found!")
            return img
        
        fg_pixels = img[is_fg].astype(np.float32)
        current_brightness = np.mean(fg_pixels) / 255.0
        
        if current_brightness < 0.01:
            logger.warning(f"adaptive_brightness: Current brightness very low ({current_brightness:.3f})")
            return img
        
        # Scale factor to reach target brightness (cap at 3x to avoid washout)
        scale = min(target_brightness / current_brightness, 3.0)
        
        if abs(scale - 1.0) > 0.05:  # Only adjust if significant difference
            result = img.astype(np.float32)
            result[is_fg] = np.clip(result[is_fg] * scale, 0, 255)
            result[~is_fg] = bg_f
            logger.debug(f"adaptive_brightness: {current_brightness:.3f} -> {target_brightness:.3f} (scale={scale:.2f})")
            return result.astype(np.uint8)
        
        return img

    @staticmethod
    def render(xs, ys, colors, width=1024, height=1024,
               xlim=(-1.3, 1.3), ylim=(-1.3, 1.3),
               cmap_name="viridis", bg=BG_RGB,
               glow=True, glow_radius=1, glow_intensity=0.18,
               use_gpu=True, brightness_boost=0.0, gamma=1.0,
               invert=False, adaptive_eq=False):
        """Enhanced render with visibility controls."""
        logger.info(f"Rendering Smooth/Glow {width}x{height} | Palette: {cmap_name} | GPU: {use_gpu and HAS_CUPY}")
        
        px, py, mask = BitmapRenderer._map_coords(xs, ys, width, height, xlim, ylim)
        
        if not np.any(mask):
            return np.full((height, width, 3), bg, dtype=np.uint8)
        
        px, py = px[mask], py[mask]
        logger.debug(f"Points in bounds: {len(px)}/{len(xs)}")
        
        c = colors[:len(px)]
        c_max = max(int(c.max()), 1)
        lut = BitmapRenderer.build_lut(cmap_name, c_max, brightness_boost, gamma, invert).astype(np.float32)
        pc = lut[c]
        flat = py.astype(np.int64) * width + px.astype(np.int64)
        n_pix = width * height
        
        if HAS_CUPY and use_gpu:
            result = render_bincount_gpu(flat, pc, height, width, bg)
        else:
            result = BitmapRenderer._render_bincount_cpu(flat, pc, height, width, n_pix, bg)
        
        if glow:
            if HAS_CUPY and use_gpu:
                result = render_glow_gpu(result, glow_radius, glow_intensity, bg)
            else:
                result = BitmapRenderer._glow_cpu(result, glow_radius, glow_intensity, bg)
        
        if adaptive_eq:
            result = BitmapRenderer.adaptive_brightness(result, 0.55, bg)
        
        # Debug: count non-background pixels
        bg_arr = np.array(bg, dtype=np.uint8)
        fg_count = np.sum(~np.all(result == bg_arr, axis=2))
        logger.info(f"Render complete: {fg_count:,} foreground pixels")
        
        return result

    @staticmethod
    def _render_bincount_cpu(flat, pc, height, width, n_pix, bg):
        img = np.zeros((height, width, 3), dtype=np.float32)
        for ch in range(3):
            img[:, :, ch] = np.bincount(flat, weights=pc[:, ch], minlength=n_pix)[:n_pix].reshape(height, width)
        weight = np.bincount(flat, minlength=n_pix)[:n_pix].reshape(height, width)
        nz = weight > 0; img[nz] /= weight[nz, np.newaxis]
        result = np.full((height, width, 3), bg, dtype=np.uint8)
        result[nz] = np.clip(img[nz], 0, 255).astype(np.uint8)
        return result

    @staticmethod
    def render_direct(xs, ys, colors, width, height, xlim, ylim, cmap_name,
                      bg=BG_RGB, brightness_boost=0.0, gamma=1.0, invert=False):
        """Enhanced direct render with visibility controls."""
        logger.info(f"Rendering Vibrant {width}x{height} | Palette: {cmap_name}")
        
        px, py, mask = BitmapRenderer._map_coords(xs, ys, width, height, xlim, ylim)
        img = np.full((height, width, 3), bg, dtype=np.uint8)
        
        if not np.any(mask):
            return img
        
        px, py = px[mask], py[mask]
        logger.debug(f"Points in bounds: {len(px)}/{len(xs)}")
        
        c = colors[mask]
        c_max = max(int(c.max()), 1)
        lut = BitmapRenderer.build_lut(cmap_name, c_max, brightness_boost, gamma, invert)
        
        # Direct pixel assignment
        img[py, px] = lut[c]
        
        # Debug: count non-background pixels
        bg_arr = np.array(bg, dtype=np.uint8)
        fg_count = np.sum(~np.all(img == bg_arr, axis=2))
        logger.info(f"Render complete: {fg_count:,} foreground pixels")
        
        return img

    @staticmethod
    def dilate(img, use_gpu=False, iterations=1):
        """Dilate image to make sparse points more visible."""
        result = img.copy()
        
        for _ in range(iterations):
            if use_gpu and HAS_CUPY:
                import cupy as cp
                from cupyx.scipy.ndimage import maximum_filter
                result = cp.asnumpy(maximum_filter(cp.asarray(result), size=3))
            else:
                h, w, _ = result.shape
                pad = np.pad(result, ((1, 1), (1, 1), (0, 0)), mode='constant', constant_values=0)
                out = np.zeros_like(result)
                for dy in range(3):
                    for dx in range(3):
                        out = np.maximum(out, pad[dy:dy+h, dx:dx+w])
                result = out
                
        return result

    @staticmethod
    def enhance_vibrancy(img, factor=1.5):
        """Enhance color saturation/vibrancy."""
        if factor == 1.0: 
            return img
        img_f = img.astype(np.float32)
        grey = np.mean(img_f, axis=2, keepdims=True)
        out = grey + (img_f - grey) * factor
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def _glow_cpu(img, radius, intensity, bg):
        """Apply glow effect using box blur."""
        h, w = img.shape[:2]
        src = img.astype(np.float32)
        k = 2 * radius + 1
        pad = np.pad(src, ((0, 0), (radius, radius), (0, 0)), mode="edge")
        cumsum = np.cumsum(pad, axis=1)
        tmp = (cumsum[:, k:, :] - cumsum[:, :-k, :]) / k
        tmp = tmp[:, :w, :]
        pad2 = np.pad(tmp, ((radius, radius), (0, 0), (0, 0)), mode="edge")
        cumsum2 = np.cumsum(pad2, axis=0)
        blurred = (cumsum2[k:, :, :] - cumsum2[:-k, :, :]) / k
        blurred = blurred[:h, :, :]
        bg_f = np.array(bg, dtype=np.float32)
        is_bg = np.all(src == bg_f, axis=2)
        out = src * (1 - intensity) + blurred * intensity
        out[is_bg] = bg_f
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def compute_bounds(xs, ys, margin=0.08):
        """Compute bounding box with margin."""
        x0, x1 = float(xs.min()), float(xs.max())
        y0, y1 = float(ys.min()), float(ys.max())
        rng = max(x1 - x0, y1 - y0, 0.01) * (1 + margin)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half = rng / 2
        return (cx - half, cx + half), (cy - half, cy + half)