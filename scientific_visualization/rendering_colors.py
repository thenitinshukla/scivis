from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

PALETTES = {
    "Jade Fire": ["#071a17", "#0b5d4d", "#19a974", "#d8f36b", "#ff9f43", "#ff3b30"],
    "Neon Pulse": ["#050018", "#3a0ca3", "#7209b7", "#f72585", "#4cc9f0", "#fef08a"],
    "Cyber Dream": ["#090b1a", "#2426a5", "#00b4d8", "#72efdd", "#f15bb5", "#fee440"],
    "Rainbow Prism": ["#5e35b1", "#1976d2", "#00a86b", "#fdd835", "#f57c00", "#d81b60"],
    "Tropical Bloom": ["#0b132b", "#3a506b", "#5bc0be", "#9bc53d", "#fde74c", "#fa7921"],
    "Solar Flare": ["#120d00", "#5b2200", "#c94800", "#ff8f00", "#ffd166", "#fff3b0"],
    "Candy Plasma": ["#10002b", "#5a189a", "#9d4edd", "#f15bb5", "#ff6f91", "#feeafa"],
    "Aurora": ["#05051a", "#0b4f6c", "#00a896", "#7ae582", "#f1fa8c", "#d6eaff"],
    "Ultraviolet": ["#090016", "#240046", "#5a189a", "#9d4edd", "#e0aaff", "#f7ecff"],
    "Ember": ["#100000", "#4a0404", "#9b2226", "#ca6702", "#ee9b00", "#ffe08a"],
    "Ocean": ["#02040f", "#023e8a", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"],
    "Spectral": ["#5e239d", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"],
    "Scientific Blue-Red": ["#313695", "#4575b4", "#74add1", "#f7f7f7", "#f46d43", "#d73027", "#a50026"],
    "Viridis": ["#440154", "#31688e", "#35b779", "#fde725"],
    "Magma": ["#000004", "#51127c", "#b73779", "#fc8961", "#fcfdbf"],
    "Grayscale": ["#050505", "#808080", "#ffffff"],
}

CYCLIC_PALETTES = {
    "Phase Twilight": ["#e56b6f", "#9d4edd", "#4361ee", "#4cc9f0", "#2a9d8f", "#f4a261", "#e56b6f"],
    "Phase Turbo": ["#30123b", "#4145ab", "#2db6a3", "#b8de29", "#f9e721", "#f8961e", "#d62828", "#30123b"],
    "HSV Phase": ["#ff0000", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ff00ff", "#ff0000"],
}

ALL_PALETTES = {**PALETTES, **CYCLIC_PALETTES}


def make_palette(name: str, reverse: bool = False, phase: float = 0.0, samples: int = 512):
    colors = ALL_PALETTES.get(name)
    if colors is None:
        raise ValueError(f"Unknown palette: {name}")
    cmap = LinearSegmentedColormap.from_list(f"custom_{name}", colors, N=samples)
    lut = cmap(np.linspace(0, 1, samples))
    if phase:
        shift = int(round((phase % 1.0) * samples))
        lut = np.roll(lut, shift, axis=0)
    if reverse:
        lut = lut[::-1]
    return LinearSegmentedColormap.from_list(f"custom_{name}_phase", lut, N=samples)


@dataclass(frozen=True)
class ColorEngineConfig:
    palette: str = "Viridis"
    reverse: bool = False
    phase: float = 0.0
    gamma: float = 1.0
    contrast: float = 1.0
    black_floor: float = 0.0
    mapping: str = "Scalar"


def palette_preview_data(name: str, n: int = 256):
    cmap = make_palette(name, samples=n)
    x = np.linspace(0, 1, n)
    return cmap(x).reshape(1, n, 4)
