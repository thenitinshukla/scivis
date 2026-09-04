"""
Modern plotting look-and-feel for Scientific Visualization (Python).

Two themes (light/dark) with clean typography, subtle grids, and no
chartjunk. Call `apply_theme(fig, theme)` right before drawing.
"""
from __future__ import annotations

import matplotlib as mpl

LIGHT = dict(
    figure_facecolor="#ffffff",
    axes_facecolor="#ffffff",
    text_color="#1a1a1a",
    grid_color="#d8d8d8",
    spine_color="#888888",
    accent="#2a6fdb",
)

DARK = dict(
    figure_facecolor="#111318",
    axes_facecolor="#171a21",
    text_color="#e8e8e8",
    grid_color="#33373f",
    spine_color="#5a5f68",
    accent="#5aa2ff",
)

THEMES = {"Light": LIGHT, "Dark": DARK}

# Colormap groupings, shown to the user by category for quicker, more
# deliberate choices than one long flat list.
COLORMAPS = {
    "Sequential": ["viridis", "plasma", "inferno", "magma", "cividis", "cubehelix"],
    "Diverging (signed fields)": ["RdBu_r", "coolwarm", "seismic", "PuOr", "PRGn"],
    "Perceptual / misc": ["turbo", "twilight_shifted", "gray"],
}
ALL_COLORMAPS = [c for group in COLORMAPS.values() for c in group]

DIVERGING_CMAPS = set(COLORMAPS["Diverging (signed fields)"])

# Qualitative line-color palettes for tracks/lineouts (index-based coloring),
# offered as named choices so results are reproducible and colorblind-aware.
LINE_PALETTES = {
    "Viridis-based": None,     # sampled from a continuous cmap at draw time
    "Okabe-Ito (colorblind-safe)": [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442",
        "#0072B2", "#D55E00", "#CC79A7", "#000000",
    ],
    "Tableau 10": [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
        "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    ],
    "Bright": [
        "#FF3B30", "#FF9500", "#FFCC00", "#34C759",
        "#00C7BE", "#30B0C7", "#007AFF", "#AF52DE",
    ],
}

DEFAULT_ACCENT = {"Light": "#2a6fdb", "Dark": "#5aa2ff"}

FONT_FAMILIES = ["DejaVu Sans", "Arial", "Helvetica", "Liberation Sans", "Times New Roman", "STIXGeneral", "Computer Modern Roman"]
_FONT_FAMILY = "DejaVu Sans"
_FONT_SIZE = 10.5

def set_font_preferences(family: str | None = None, size: float | None = None):
    global _FONT_FAMILY, _FONT_SIZE
    if family:
        _FONT_FAMILY = family
    if size is not None:
        _FONT_SIZE = float(size)
    mpl.rcParams["font.family"] = _FONT_FAMILY
    mpl.rcParams["font.size"] = _FONT_SIZE
    mpl.rcParams["axes.titlesize"] = _FONT_SIZE * 1.15
    mpl.rcParams["axes.labelsize"] = _FONT_SIZE
    mpl.rcParams["xtick.labelsize"] = max(6.0, _FONT_SIZE * 0.9)
    mpl.rcParams["ytick.labelsize"] = max(6.0, _FONT_SIZE * 0.9)
    mpl.rcParams["legend.fontsize"] = max(6.0, _FONT_SIZE * 0.9)

def current_font_preferences():
    return _FONT_FAMILY, _FONT_SIZE


def line_color_cycle(palette_name: str, n: int, cmap_fallback: str = "viridis"):
    """Return a list of `n` hex colors for index-based line coloring."""
    import matplotlib.cm as cm
    palette = LINE_PALETTES.get(palette_name)
    if palette:
        return [palette[i % len(palette)] for i in range(n)]
    cmap = cm.get_cmap(cmap_fallback, max(n, 1))
    return [cmap(i) for i in range(n)]


def base_rcparams():
    """Global rcParams applied once at app start -- modern, minimal chrome."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "medium",
        "axes.labelsize": 10.5,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "axes.linewidth": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "image.interpolation": "nearest",
    })


def apply_theme(fig, theme_name: str = "Light"):
    """Apply colors for the given theme to a Figure and all its Axes."""
    t = THEMES.get(theme_name, LIGHT)
    fig.set_facecolor(t["figure_facecolor"])
    for ax in fig.get_axes():
        ax.set_facecolor(t["axes_facecolor"])
        ax.title.set_color(t["text_color"])
        ax.xaxis.label.set_color(t["text_color"])
        ax.yaxis.label.set_color(t["text_color"])
        family, size = current_font_preferences()
        ax.title.set_fontfamily(family); ax.title.set_fontsize(size * 1.15)
        ax.xaxis.label.set_fontfamily(family); ax.xaxis.label.set_fontsize(size)
        ax.yaxis.label.set_fontfamily(family); ax.yaxis.label.set_fontsize(size)
        ax.tick_params(colors=t["text_color"], labelsize=max(6.0, size * 0.9))
        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontfamily(family)
        for spine in ax.spines.values():
            spine.set_color(t["spine_color"])
        ax.grid(True, color=t["grid_color"], linewidth=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        legend = ax.get_legend()
        if legend is not None:
            for text in legend.get_texts():
                text.set_color(t["text_color"])
    return t


# ---------------------------------------------------------------------
# Whole-application (Qt widget chrome) dark/light mode -- distinct from
# the per-figure `apply_theme` above but meant to be kept in sync with it
# by the main window, so "Dark" means the whole app goes dark, not just
# the plots.
# ---------------------------------------------------------------------

LIGHT_QSS = ""  # empty stylesheet == Qt platform default light look

DARK_QSS = """
QWidget {
    background-color: #202226;
    color: #e8e8e8;
    selection-background-color: #3a6fd8;
    selection-color: #ffffff;
}
QMainWindow, QScrollArea, QSplitter {
    background-color: #202226;
}
QGroupBox {
    border: 1px solid #3a3d44;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #cfd3da;
}
QPushButton {
    background-color: #33363d;
    border: 1px solid #45484f;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover { background-color: #3d4148; }
QPushButton:pressed { background-color: #2a2d33; }
QComboBox, QSpinBox, QDoubleSpinBox, QListWidget, QLineEdit {
    background-color: #2a2d33;
    border: 1px solid #45484f;
    border-radius: 4px;
    padding: 3px;
}
QComboBox QAbstractItemView {
    background-color: #2a2d33;
    selection-background-color: #3a6fd8;
}
QTabWidget::pane { border: 1px solid #3a3d44; }
QTabBar::tab {
    background: #2a2d33;
    padding: 6px 14px;
    border: 1px solid #3a3d44;
    border-bottom: none;
}
QTabBar::tab:selected { background: #33363d; color: #ffffff; }
QScrollBar:vertical {
    background: #202226;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #45484f;
    border-radius: 5px;
    min-height: 24px;
}
QToolBar { background-color: #26282c; border: none; spacing: 6px; }
QLabel { background: transparent; }
QCheckBox, QRadioButton { spacing: 6px; }
"""


def apply_app_theme(app, theme_name: str):
    """Apply (or remove) the whole-application dark stylesheet."""
    app.setStyleSheet(DARK_QSS if theme_name == "Dark" else LIGHT_QSS)
