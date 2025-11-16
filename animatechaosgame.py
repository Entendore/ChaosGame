import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.animation import FuncAnimation, PillowWriter
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import shutil

class ChaosGameFractal:
    """Generates and animates fractals using the Chaos Game algorithm with optimized rendering."""
    
    def __init__(
        self,
        fractal_configs: List[Dict[str, Any]],
        points_per_fractal: int = 500_000,
        batch_size: Optional[int] = None,
        dpi: int = 100,
        figure_size: Tuple[float, float] = (8, 8),
        output_dir: str = "fractal_gifs"
    ):
        """
        Initialize the fractal gallery with configuration options.
        
        Args:
            fractal_configs: List of fractal configuration dictionaries
            points_per_fractal: Number of points to generate per fractal
            batch_size: Points to render per animation frame (auto-calculated if None)
            dpi: Dots per inch for rendering
            figure_size: Figure dimensions in inches (width, height)
            output_dir: Directory for saving GIFs
        """
        self.fractal_configs = fractal_configs
        self.points_per_fractal = points_per_fractal
        self.batch_size = batch_size
        self.dpi = dpi
        self.figure_size = figure_size
        self.output_dir = Path(output_dir)
        self._fractal_data: List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
        self._figure: Optional[plt.Figure] = None
        self._ax: Optional[plt.Axes] = None
        self._scatter: Any = None
        self._title: Optional[plt.Text] = None
        self._current_fractal: int = 0
        self._batches_per_fractal: int = 0
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def _generate_vertices(self, config: Dict[str, Any]) -> np.ndarray:
        """Generate polygon vertices based on configuration."""
        n = config["vertices"]
        if config.get("random_vertices", False):
            return self._random_polygon_vertices(n)
        return self._regular_polygon_vertices(n)
    
    @staticmethod
    def _regular_polygon_vertices(n: int, radius: float = 1.0) -> np.ndarray:
        """Generate vertices for a regular polygon."""
        angles = np.linspace(math.pi/2, math.pi/2 + 2*math.pi, n, endpoint=False)
        return np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))
    
    @staticmethod
    def _random_polygon_vertices(n: int, radius: float = 1.0) -> np.ndarray:
        """Generate vertices with random angles for an irregular polygon."""
        angles = np.sort(np.random.random(n) * 2 * math.pi)
        return np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))
    
    def _chaos_game(
        self,
        vertices: np.ndarray,
        r: float = 0.5,
        no_repeat: bool = False,
        skip: int = 0,
        seed: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate fractal points using the Chaos Game algorithm.
        
        Returns:
            xs, ys: Coordinate arrays
            colors: Color gradient array
        """
        if seed is not None:
            np.random.seed(seed)
        
        n_vertices = len(vertices)
        vx, vy = vertices[:, 0], vertices[:, 1]
        x, y = vx[0], vy[0]
        prev_idx = 0
        
        xs = np.empty(self.points_per_fractal, dtype=np.float32)
        ys = np.empty(self.points_per_fractal, dtype=np.float32)
        colors = np.linspace(0, 1, self.points_per_fractal, dtype=np.float32)
        
        # Precompute random indices
        indices = np.random.randint(0, n_vertices, self.points_per_fractal)
        
        # Apply constraints efficiently
        if no_repeat or skip > 0:
            for i in range(1, self.points_per_fractal):
                idx = indices[i]
                if no_repeat and idx == prev_idx:
                    idx = (idx + 1) % n_vertices
                if skip > 0:
                    circular_dist = min(abs(idx - prev_idx), n_vertices - abs(idx - prev_idx))
                    if circular_dist <= skip:
                        idx = (prev_idx + skip + 1) % n_vertices
                indices[i] = idx
                prev_idx = idx
        
        # Generate points
        for i in range(self.points_per_fractal):
            idx = indices[i]
            x += r * (vx[idx] - x)
            y += r * (vy[idx] - y)
            xs[i] = x
            ys[i] = y
        
        return xs, ys, colors
    
    def precompute(self) -> None:
        """Precompute all fractal data in background threads."""
        print("Precomputing fractals (this may take 10-15 seconds)...")
        start_time = time.time()
        
        with ThreadPoolExecutor() as executor:
            futures = []
            for i, config in enumerate(self.fractal_configs):
                seed = 42 + i
                vertices = self._generate_vertices(config)
                future = executor.submit(
                    self._chaos_game,
                    vertices,
                    r=config.get("r", 0.5),
                    no_repeat=config.get("no_repeat", False),
                    skip=config.get("skip", 0),
                    seed=seed
                )
                futures.append((future, config))
            
            self._fractal_data = []
            for future, config in futures:
                xs, ys, colors = future.result()
                point_size = config.get("point_size", 0.4)
                sizes = np.full(self.points_per_fractal, point_size, dtype=np.float32)
                self._fractal_data.append((xs, ys, colors, sizes))
        
        print(f"Precomputation completed in {time.time() - start_time:.2f} seconds")
    
    def _measure_optimal_batch_size(self) -> int:
        """Determine optimal batch size for smooth animation on current hardware."""
        test_points = 100_000
        test_offsets = np.random.rand(test_points, 2) * 3.6 - 1.8
        
        # Create temporary figure for benchmarking
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        ax.set_xlim(-1.8, 1.8)
        ax.set_ylim(-1.8, 1.8)
        scatter = ax.scatter(test_offsets[:, 0], test_offsets[:, 1], s=0.3, alpha=0.7)
        
        start = time.perf_counter()
        scatter.set_offsets(test_offsets)
        fig.canvas.draw()
        render_time = time.perf_counter() - start
        
        plt.close(fig)  # Clean up temporary figure
        
        # Calculate batch size for target 30 FPS
        points_per_frame = int(1 / (render_time / test_points) / 30)
        return max(2000, min(20000, points_per_frame))  # Clamp between 2k-20k
    
    def _setup_figure(self, dark_theme: bool = True) -> Tuple[plt.Figure, plt.Axes]:
        """Initialize a figure and axes with consistent styling."""
        fig, ax = plt.subplots(
            figsize=self.figure_size,
            dpi=self.dpi,
            facecolor='black' if dark_theme else 'white'
        )
        ax.set_facecolor('black' if dark_theme else 'white')
        ax.set_xlim(-1.8, 1.8)
        ax.set_ylim(-1.8, 1.8)
        ax.axis("off")
        fig.tight_layout(pad=0)
        return fig, ax
    
    def _update(self, frame: int) -> Tuple[Any, plt.Text]:
        """Animation update function."""
        # Calculate current fractal and batch
        current_fractal = frame // self._batches_per_fractal
        batch_idx = frame % self._batches_per_fractal
        
        # Get data for current fractal
        xs, ys, colors, sizes = self._fractal_data[current_fractal]
        config = self.fractal_configs[current_fractal]
        
        # Calculate end index for current batch
        end_index = min((batch_idx + 1) * self.batch_size, self.points_per_fractal)
        
        # Update scatter plot
        self._scatter.set_offsets(np.column_stack((xs[:end_index], ys[:end_index])))
        self._scatter.set_array(colors[:end_index])
        self._scatter.set_sizes(sizes[:end_index])
        self._scatter.set_cmap(config.get("colormap", "viridis"))
        
        # Update title when starting new fractal
        if batch_idx == 0:
            self._title.set_text(config["title"])
        
        return self._scatter, self._title
    
    def animate(self) -> None:
        """Start the interactive animation after precomputation."""
        if not self._fractal_data:
            raise RuntimeError("Call precompute() before animate()")
        
        # Determine batch size if not specified
        if self.batch_size is None:
            self.batch_size = self._measure_optimal_batch_size()
            print(f"Optimized batch size: {self.batch_size} points/frame")
        
        # Calculate batches per fractal
        self._batches_per_fractal = (self.points_per_fractal + self.batch_size - 1) // self.batch_size
        
        # Setup visualization
        self._figure, self._ax = self._setup_figure()
        
        # Initialize scatter plot with color data
        xs, ys, colors, sizes = self._fractal_data[0]
        self._scatter = self._ax.scatter(
            xs[:1], ys[:1],
            c=colors[:1],  # Provide color data to avoid warning
            s=sizes[0],
            cmap=self.fractal_configs[0].get("colormap", "viridis"),
            alpha=0.8,
            linewidth=0,
            marker='.',
            vmin=0, vmax=1
        )
        
        # Initialize title
        self._title = self._ax.text(
            0.5, 0.95,
            self.fractal_configs[0]["title"],
            ha='center', va='center',
            transform=self._figure.transFigure,
            fontsize=14, color='white',
            bbox=dict(facecolor='black', alpha=0.8, edgecolor='none')
        )
        
        # Create animation
        total_frames = self._batches_per_fractal * len(self.fractal_configs)
        anim = FuncAnimation(
            self._figure,
            self._update,
            frames=total_frames,
            interval=30,  # Target 30 FPS
            blit=True,
            repeat=True
        )
        
        plt.show()
    
    def generate_gifs(
        self,
        duration_seconds: float = 5.0,
        fps: int = 30,
        max_points: Optional[int] = None,
        overwrite: bool = False
    ) -> None:
        """
        Generate GIFs for each fractal configuration.
        
        Args:
            duration_seconds: Duration of each GIF in seconds
            fps: Frames per second for the GIFs
            max_points: Maximum points to render per fractal (None = use all points)
            overwrite: Whether to overwrite existing GIF files
        """
        if not self._fractal_data:
            print("Precomputing fractal data...")
            self.precompute()
        
        # Calculate frames and batch size
        total_frames = int(duration_seconds * fps)
        points_to_render = max_points if max_points is not None else self.points_per_fractal
        batch_size = max(1, points_to_render // total_frames)
        print(f"Generating GIFs: {duration_seconds}s duration, {fps} FPS, {total_frames} frames per GIF")
        
        try:
            for i, (config, (xs, ys, colors, sizes)) in enumerate(zip(self.fractal_configs, self._fractal_data)):
                filename = self._sanitize_filename(config["title"]) + ".gif"
                output_path = self.output_dir / filename
                
                # Skip if file exists and overwrite is False
                if output_path.exists() and not overwrite:
                    print(f"Skipping existing GIF: {filename}")
                    continue
                
                print(f"\nGenerating GIF {i+1}/{len(self.fractal_configs)}: {config['title']}")
                
                # Create figure for this fractal
                fig, ax = self._setup_figure()
                
                # Initialize scatter with first point and color data
                scatter = ax.scatter(
                    xs[:1], ys[:1],
                    c=colors[:1],  # Provide color data to avoid warning
                    s=sizes[:1],
                    cmap=config.get("colormap", "viridis"),
                    alpha=0.8,
                    linewidth=0,
                    marker='.',
                    vmin=0, vmax=1
                )
                
                # Add title
                title = ax.text(
                    0.5, 0.95,
                    config["title"],
                    ha='center', va='center',
                    transform=fig.transFigure,
                    fontsize=14, color='white',
                    bbox=dict(facecolor='black', alpha=0.8, edgecolor='none')
                )
                
                # Progress tracking
                progress_step = max(1, total_frames // 10)
                
                def update_gif_frame(frame_idx):
                    """Update function for GIF animation."""
                    if frame_idx % progress_step == 0:
                        progress = (frame_idx / total_frames) * 100
                        print(f"  Progress: {progress:.1f}% ({frame_idx}/{total_frames})", end='\r')
                    
                    # Calculate how many points to show in this frame
                    points_idx = min((frame_idx + 1) * batch_size, points_to_render)
                    scatter.set_offsets(np.column_stack((xs[:points_idx], ys[:points_idx])))
                    scatter.set_array(colors[:points_idx])
                    scatter.set_sizes(sizes[:points_idx])
                    return scatter, title
                
                # Create animation
                anim = FuncAnimation(
                    fig,
                    update_gif_frame,
                    frames=total_frames,
                    interval=1000/fps,
                    blit=True
                )
                
                # Save as GIF
                writer = PillowWriter(fps=fps, metadata=dict(artist='ChaosGameFractal'))
                anim.save(str(output_path), writer=writer, dpi=self.dpi)
                
                # Cleanup
                plt.close(fig)
                print(f"\nSaved: {output_path}")
        
        except Exception as e:
            print(f"Error generating GIFs: {e}")
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip('. ')
    
    def run(self) -> None:
        """Complete workflow: precompute and animate."""
        self.precompute()
        self.animate()


def clear_gif_directory(output_dir: str = "fractal_gifs") -> None:
    """Clear the GIF output directory (use with caution)."""
    dir_path = Path(output_dir)
    if dir_path.exists():
        print(f"Clearing directory: {dir_path}")
        for file in dir_path.glob("*.gif"):
            file.unlink()
        print("Directory cleared.")
    else:
        print(f"Directory does not exist: {dir_path}")


def main() -> None:
    """Configure and run the fractal animation gallery or generate GIFs."""
    fractal_configs = [
        {"vertices": 3, "r": 0.5, "title": "Sierpinski Triangle", "colormap": "viridis", "point_size": 0.3},
        {"vertices": 4, "r": 0.5, "skip": 1, "title": "Square Maze", "colormap": "inferno", "point_size": 0.25},
        {"vertices": 5, "r": 0.618, "title": "Golden Pentagon", "colormap": "cividis", "point_size": 0.3},
        {"vertices": 5, "r": 0.618, "skip": 1, "title": "Pentagram Void", "colormap": "twilight", "point_size": 0.35},
        {"vertices": 6, "r": 0.5, "title": "Hexagonal Snowflake", "colormap": "plasma", "point_size": 0.25},
        {"vertices": 6, "r": 0.5, "skip": 2, "title": "Star of David", "colormap": "magma", "point_size": 0.4},
        {"vertices": 7, "r": 0.5, "random_vertices": True, "title": "Chaotic Heptagon", "colormap": "hot", "point_size": 0.3},
        {"vertices": 8, "r": 0.5, "title": "Octagonal Vortex", "colormap": "cubehelix", "point_size": 0.2},
        {"vertices": 9, "r": 0.45, "skip": 1, "title": "Nonagonal Nebula", "colormap": "nipy_spectral", "point_size": 0.25},
        {"vertices": 10, "r": 0.5, "title": "Decagonal Bloom", "colormap": "gist_earth", "point_size": 0.2},
        {"vertices": 12, "r": 0.5, "title": "Dodecagonal Cosmos", "colormap": "rainbow", "point_size": 0.15},
    ]
    
    # Create gallery instance
    gallery = ChaosGameFractal(
        fractal_configs=fractal_configs,
        points_per_fractal=300_000,  # Reduced for faster GIF generation
        dpi=100,
        figure_size=(10, 10),
        output_dir="fractal_gifs"
    )
    
    # Option 1: Generate GIFs for all fractals
    print("\n" + "="*50)
    print("GENERATING FRACTAL GIFS")
    print("="*50)
    
    # Optional: Clear existing GIFs first
    # clear_gif_directory("fractal_gifs")
    
    gallery.generate_gifs(
        duration_seconds=3.0,  # 3 seconds per GIF
        fps=20,               # Standard GIF frame rate
        max_points=150_000,   # Reduce points for smaller file sizes
        overwrite=False       # Set to True to regenerate existing GIFs
    )
    
    # Option 2: Run interactive animation (uncomment to use)
    # print("\n" + "="*50)
    # print("STARTING INTERACTIVE ANIMATION")
    # print("="*50)
    # gallery.run()


if __name__ == "__main__":
    main()