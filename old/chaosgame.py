import matplotlib.pyplot as plt
import numpy as np
import random
import math
import os
from typing import List, Tuple, Optional, Dict, Any


class PolygonGenerator:
    """Generates polygon vertices in regular or random configurations."""
    
    @staticmethod
    def regular(n: int, radius: float = 1.0, center: Tuple[float, float] = (0, 0), 
               start_angle: float = math.pi/2) -> List[Tuple[float, float]]:
        """
        Generate vertices of a regular polygon.
        
        Args:
            n: Number of vertices
            radius: Distance from center to vertices
            center: Center point of the polygon
            start_angle: Starting angle for first vertex (default: pi/2 for top vertex)
            
        Returns:
            List of (x, y) coordinates for each vertex
        """
        cx, cy = center
        return [
            (
                cx + radius * math.cos(start_angle + 2 * math.pi * k / n),
                cy + radius * math.sin(start_angle + 2 * math.pi * k / n)
            )
            for k in range(n)
        ]
    
    @staticmethod
    def random(n: int, radius: float = 1.0) -> List[Tuple[float, float]]:
        """
        Generate vertices of a random convex polygon.
        
        Args:
            n: Number of vertices
            radius: Maximum distance from origin
            
        Returns:
            List of (x, y) coordinates for each vertex
        """
        angles = np.sort(np.random.rand(n) * 2 * math.pi)
        return [(math.cos(t) * radius, math.sin(t) * radius) for t in angles]


class ChaosGame:
    """Generates fractal patterns using the chaos game algorithm."""
    
    def __init__(
        self,
        vertices: int,
        r: Optional[float] = 0.5,
        skip: int = 0,
        random_vertices: bool = False,
        no_repeat: bool = False,
        burn_in: int = 50,
        iterations: int = 200_000
    ):
        """
        Initialize chaos game parameters.
        
        Args:
            vertices: Number of polygon vertices
            r: Contraction ratio (None for random ratio per step)
            skip: Minimum vertex skip distance (for star patterns)
            random_vertices: Use random polygon vertices
            no_repeat: Prevent consecutive vertex selection
            burn_in: Number of initial points to discard
            iterations: Number of points to generate after burn-in
        """
        self.vertices = vertices
        self.r = r
        self.skip = skip
        self.random_vertices = random_vertices
        self.no_repeat = no_repeat
        self.burn_in = burn_in
        self.iterations = iterations
        self.total_points = iterations + burn_in
        
        # Generate vertices and precompute arrays
        self.verts = (
            PolygonGenerator.random(vertices) 
            if random_vertices 
            else PolygonGenerator.regular(vertices)
        )
        self.vx = np.array([v[0] for v in self.verts])
        self.vy = np.array([v[1] for v in self.verts])
        
        # Precompute valid transitions for skip patterns
        self._valid_transitions = None
        if skip > 0:
            self._precompute_valid_transitions()
    
    def _precompute_valid_transitions(self) -> None:
        """Precompute valid vertex transitions considering skip constraints."""
        self._valid_transitions = []
        for i in range(self.vertices):
            valid = [
                j for j in range(self.vertices)
                if min(abs(i - j), self.vertices - abs(i - j)) > self.skip
            ]
            # Fallback to all vertices if no valid transitions exist
            self._valid_transitions.append(valid if valid else list(range(self.vertices)))
    
    def _standard_game(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run standard chaos game with optional no-repeat constraint."""
        xs, ys, colors = [], [], []
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        prev_idx = None
        
        for i in range(self.total_points):
            idx = random.randrange(self.vertices)
            if self.no_repeat and prev_idx is not None:
                while idx == prev_idx:
                    idx = random.randrange(self.vertices)
            
            x += self.r * (self.vx[idx] - x)
            y += self.r * (self.vy[idx] - y)
            prev_idx = idx
            
            if i >= self.burn_in:
                xs.append(x)
                ys.append(y)
                colors.append(idx)
        
        return np.array(xs), np.array(ys), np.array(colors)
    
    def _random_ratio_game(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run chaos game with random contraction ratio per step."""
        xs, ys, colors = [], [], []
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        
        for i in range(self.total_points):
            idx = random.randrange(self.vertices)
            r_step = random.uniform(0.3, 0.7)
            
            x += r_step * (self.vx[idx] - x)
            y += r_step * (self.vy[idx] - y)
            
            if i >= self.burn_in:
                xs.append(x)
                ys.append(y)
                colors.append(idx)
        
        return np.array(xs), np.array(ys), np.array(colors)
    
    def _skip_game(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run chaos game with vertex skipping constraint."""
        xs, ys, colors = [], [], []
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        prev_idx = random.randrange(self.vertices)
        
        for i in range(self.total_points):
            idx = random.choice(self._valid_transitions[prev_idx])
            
            x += self.r * (self.vx[idx] - x)
            y += self.r * (self.vy[idx] - y)
            prev_idx = idx
            
            if i >= self.burn_in:
                xs.append(x)
                ys.append(y)
                colors.append(idx)
        
        return np.array(xs), np.array(ys), np.array(colors)
    
    def generate(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate fractal points based on configuration."""
        if self.r is None:
            return self._random_ratio_game()
        elif self.skip > 0:
            return self._skip_game()
        else:
            return self._standard_game()


class FractalPlotter:
    """Handles visualization of fractal patterns."""
    
    @staticmethod
    def plot(
        xs: np.ndarray,
        ys: np.ndarray,
        colors: np.ndarray,
        title: Optional[str] = None,
        colormap: str = "tab10",
        figsize: Tuple[int, int] = (6, 6),
        dpi: int = 150,
        marker_size: float = 0.1,
        save_path: Optional[str] = None,
        show: bool = False
    ) -> None:
        """
        Render fractal pattern with matplotlib.
        
        Args:
            xs: X coordinates of points
            ys: Y coordinates of points
            colors: Color values for each point
            title: Plot title
            colormap: Matplotlib colormap name
            figsize: Figure size in inches
            dpi: Figure resolution
            marker_size: Size of each point marker
            save_path: Path to save the image (if None, don't save)
            show: Whether to display the plot interactively
        """
        plt.figure(figsize=figsize, dpi=dpi)
        plt.scatter(xs, ys, c=colors, cmap=colormap, s=marker_size, marker=".")
        plt.axis("equal")
        plt.axis("off")
        
        if title:
            plt.title(title, fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1)
            print(f"Saved: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()  # Close the figure to free memory


def main() -> None:
    """Generate and display fractal gallery."""
    gallery_configurations: List[Dict[str, Any]] = [
        {"vertices": 3, "r": 0.5, "title": "Sierpinski Triangle", "colormap": "viridis"},
        {"vertices": 4, "r": 0.5, "no_repeat": True, "title": "Square Chaos Game", "colormap": "plasma"},
        {"vertices": 5, "r": 0.618, "title": "Pentagon Golden Ratio", "colormap": "cividis"},
        {"vertices": 6, "r": 1/3, "title": "Hexagon Variant", "colormap": "tab10"},
        {"vertices": 3, "r": None, "title": "Triangle Random r", "colormap": "magma"},
        {"vertices": 5, "r": 0.618, "skip": 1, "title": "Pentagram Chaos Game", "colormap": "cool"},
        {"vertices": 7, "r": 0.5, "random_vertices": True, "title": "Random Heptagon", "colormap": "plasma"},
        {"vertices": 8, "r": 0.618, "title": "Octagon Golden Ratio", "colormap": "cividis"},
        {"vertices": 10, "r": 0.7, "title": "Decagon Chaos", "colormap": "magma"},
        {"vertices": 12, "r": 0.5, "title": "Dodecagon Fractal", "colormap": "tab20"}
    ]
    
    # Create output directory
    output_dir = "fractal_gallery"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating fractal gallery and saving to {output_dir}/...")
    
    for i, config in enumerate(gallery_configurations, 1):
        print(f"Generating fractal {i}/{len(gallery_configurations)}: {config['title']}")
        
        game = ChaosGame(
            vertices=config["vertices"],
            r=config.get("r", 0.5),
            skip=config.get("skip", 0),
            random_vertices=config.get("random_vertices", False),
            no_repeat=config.get("no_repeat", False),
            burn_in=50,
            iterations=200_000
        )
        
        xs, ys, colors = game.generate()
        
        # Create a safe filename from the title
        safe_title = config['title'].replace(' ', '_').replace('/', '_')
        filename = f"{i:02d}_{safe_title}.png"
        save_path = os.path.join(output_dir, filename)
        
        FractalPlotter.plot(
            xs, ys, colors,
            title=config.get("title"),
            colormap=config.get("colormap", "tab10"),
            save_path=save_path,
            show=False  # Don't show interactively
        )
    
    print(f"\nAll fractals saved successfully to {output_dir}/!")


def demo_custom_fractal() -> None:
    """Demonstrate how to create a custom fractal configuration."""
    print("\n--- Custom Fractal Demo ---")
    print("Creating a custom star fractal with 7 vertices...")
    
    # Create output directory if it doesn't exist
    output_dir = "fractal_gallery"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a custom configuration
    custom_game = ChaosGame(
        vertices=7,           # Heptagon
        r=0.4,                # Contraction ratio
        skip=2,               # Skip 2 vertices for star pattern
        burn_in=100,          # More burn-in for cleaner result
        iterations=300_000    # More points for detail
    )
    
    xs, ys, colors = custom_game.generate()
    
    filename = "custom_7_point_star.png"
    save_path = os.path.join(output_dir, filename)
    
    FractalPlotter.plot(
        xs, ys, colors,
        title="Custom 7-Point Star Fractal",
        colormap="twilight",
        figsize=(8, 8),
        marker_size=0.05,
        save_path=save_path,
        show=False
    )
    
    print(f"Custom fractal saved to {save_path}")


if __name__ == "__main__":
    # Run the main gallery
    main()
    
    # Run custom demo
    demo_custom_fractal()