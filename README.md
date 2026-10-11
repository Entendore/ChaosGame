<div align="center">

# 🌌 Chaos Game Fractal Gallery  
### *A high-performance generative fractal visualizer with animation & export tools.*

<img src="fractal_gifs/Sierpinski_Triangle.gif" width="260"/>  
<br/>

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![NumPy](https://img.shields.io/badge/NumPy-optimized-success.svg)
![Matplotlib](https://img.shields.io/badge/Matplotlib-animated-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

</div>

---

## ✨ Overview

**Chaos Game Fractal Gallery** is a full-featured, performance-optimized system for generating, animating, and exporting high-resolution **Chaos Game fractals**.  
It supports regular polygons, random shapes, skip-rules, color gradients, and custom rendering styles.

Whether you're studying dynamical systems, creating art, or generating visuals for videos — this tool produces **fast, clean, mathematically precise fractals**.

---

## ⚡ Features

- 🧮 **Multi-threaded point generation** (NumPy + ThreadPoolExecutor)  
- 🌀 **Real-time animation** using Matplotlib  
- 🎨 **Customizable colors, point sizes, colormaps**  
- 🔁 **Skip-rules & no-repeat rules** for exotic fractal structures  
- 📸 **High-quality still images**  
- 🎞️ **Smooth GIF exports** with progress tracking  
- 🚀 **Adaptive batch auto-tuning** for optimal FPS  
- 🗄️ Organized output in:
  - `fractal_gallery/` — images  
  - `fractal_gifs/` — GIF animations  

---

# 🖼️ Image Gallery (`fractal_gallery/`)

### *High-resolution still frames generated from the Chaos Game.*

| | | |
|---|---|---|
| <img src="fractal_gallery/Sierpinski_Triangle.png" width="250"/> | <img src="fractal_gallery/Square_Chaos_Game.png" width="250"/> | <img src="fractal_gallery/Pentagon_Golden_Ratio.png" width="250"/> |
| **Sierpinski Triangle** | **Square Maze** | **Golden Pentagon** |
| <img src="fractal_gallery/Pentagram_Chaos_Game.png" width="250"/> | <img src="fractal_gallery/Hexagon_Variant.png" width="250"/> | <img src="fractal_gallery/custom_7_point_star.png" width="250"/> |
| **Pentagram Void** | **Hexagonal Snowflake** | **7 Point Star** |
| <img src="fractal_gallery/Random_Heptagon.png" width="250"/> | <img src="fractal_gallery/Octagon_Golden_Ratio.png" width="250"/> | <img src="fractal_gallery/Triangle_Random_r.png" width="250"/> |
| **Chaotic Heptagon** | **Octagonal Vortex** | **Triangle Random r** |
| <img src="fractal_gallery/Decagon_Chaos.png" width="250"/> | <img src="fractal_gallery/Dodecagon_Fractal.png" width="250"/> | |
| **Decagonal Bloom** | **Dodecagonal Cosmos** | |

---

# 🎞️ GIF Animation Gallery (`fractal_gifs/`)

### *Watch the fractals form themselves point-by-point in real time.*

| | | |
|---|---|---|
| <img src="fractal_gifs/Sierpinski_Triangle.gif" width="250"/> | <img src="fractal_gifs/Square_Maze.gif" width="250"/> | <img src="fractal_gifs/Golden_Pentagon.gif" width="250"/> |
| **Sierpinski Triangle** | **Square Maze** | **Golden Pentagon** |
| <img src="fractal_gifs/Pentagram_Void.gif" width="250"/> | <img src="fractal_gifs/Hexagonal_Snowflake.gif" width="250"/> | <img src="fractal_gifs/Star_of_David.gif" width="250"/> |
| **Pentagram Void** | **Hexagonal Snowflake** | **Star of David** |
| <img src="fractal_gifs/Chaotic_Heptagon.gif" width="250"/> | <img src="fractal_gifs/Octagonal_Vortex.gif" width="250"/> | <img src="fractal_gifs/Nonagonal_Nebula.gif" width="250"/> |
| **Chaotic Heptagon** | **Octagonal Vortex** | **Nonagonal Nebula** |
| <img src="fractal_gifs/Decagonal_Bloom.gif" width="250"/> | <img src="fractal_gifs/Dodecagonal_Cosmos.gif" width="250"/> | |
| **Decagonal Bloom** | **Dodecagonal Cosmos** | |

---

# 🚀 Getting Started

## 📦 Installation

```bash
pip install numpy matplotlib

python chaosgame.py
python animatechaosgame.py