"""
style.py
Shared matplotlib style and color palette for all figures.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# ── Colors ────────────────────────────────────────────────────────────────────
RED    = "#DC3520"
BLUE   = "#1F77B4"
ORANGE = "#FF7F0E"
GRAY   = "#999999"
GREEN  = "#2CA02C"

ALPHA_BAR  = 0.75
ALPHA_FILL = 0.20

# ── Figure defaults ───────────────────────────────────────────────────────────
FIG_W  = 7.0   # single-panel width (inches)
FIG_H  = 4.5   # single-panel height
FIG_DW = 12.0  # double-panel width
FIG_DH = 4.5   # double-panel height
DPI    = 150


def apply_style() -> None:
    """Call once at the top of any script or main() to set global rcParams."""
    mpl.rcParams.update({
        "figure.dpi":         DPI,
        "figure.facecolor":   "white",
        "axes.facecolor":     "white",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.grid":          True,
        "axes.grid.axis":     "y",
        "grid.color":         "#E5E5E5",
        "grid.linewidth":     0.8,
        "font.family":        "sans-serif",
        "font.size":          11,
        "axes.titlesize":     12,
        "axes.titleweight":   "bold",
        "axes.labelsize":     10,
        "xtick.labelsize":    9,
        "ytick.labelsize":    9,
        "legend.fontsize":    9,
        "legend.frameon":     False,
        "figure.constrained_layout.use": True,
    })


def save(fig: plt.Figure, path: str) -> None:
    """Save figure and close it."""
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved → {path}")
