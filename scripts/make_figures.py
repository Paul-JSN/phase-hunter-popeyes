"""Render the figures used in the README and the draft.

    python3 scripts/make_figures.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.reference import (ANTIPHASE, FERRO, FLOATING, PARA, bkt_transition, ising_transition,
                           kt_transition)

TEAL, ORANGE, PURPLE, BLUE = "#007F7A", "#D4742B", "#7356A6", "#377CA8"
NAVY, MUTED, LINE = "#152638", "#546573", "#DCE4E7"
PHASE_COLORS = ListedColormap([TEAL, ORANGE, PURPLE, BLUE])
EXTENT = [0, 1, 0, 2]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": LINE, "axes.labelcolor": NAVY,
                     "text.color": NAVY, "xtick.color": MUTED, "ytick.color": MUTED})


def overlay(axis, color="white", linewidth=1.5):
    left = np.linspace(0.001, 0.499, 200)
    right = np.linspace(0.5, 1.0, 200)
    axis.plot(left, ising_transition(left), color=color, lw=linewidth, label="Ising")
    axis.plot(right, bkt_transition(right), color=color, lw=linewidth, ls="--", label="BKT")
    axis.plot(right, kt_transition(right), color=color, lw=linewidth, ls=":", label="KT")


def frame(axis, title):
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 2)
    axis.set_xlabel(r"$\kappa$ (frustration)")
    axis.set_ylabel(r"$h$ (field)")
    axis.set_title(title, fontsize=9.5)


def main() -> None:
    data = np.load(ROOT / "data/grid_N8.npz")
    summary = json.loads((ROOT / "data/summary.json").read_text())
    zz1, zz2 = data["zz1"], data["zz2"]
    reference, predicted = data["reference"], data["predicted"]
    (ROOT / "figures").mkdir(exist_ok=True)

    figure, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    image = axes[0].imshow(zz1, origin="lower", extent=EXTENT, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    figure.colorbar(image, ax=axes[0], shrink=0.85, pad=0.02)
    overlay(axes[0])
    frame(axes[0], r"$\langle Z_i Z_{i+1}\rangle$ (nearest neighbour)")

    image = axes[1].imshow(zz2, origin="lower", extent=EXTENT, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
    figure.colorbar(image, ax=axes[1], shrink=0.85, pad=0.02)
    overlay(axes[1])
    frame(axes[1], r"$\langle Z_i Z_{i+2}\rangle$ (next-nearest)")

    axes[2].imshow(reference, origin="lower", extent=EXTENT, aspect="auto", cmap=PHASE_COLORS,
                   vmin=0, vmax=3, interpolation="nearest")
    overlay(axes[2])
    frame(axes[2], "Reference phases (analytic lines)")
    for text, x, y in [("FERRO", 0.2, 0.35), ("PARA", 0.55, 1.55), ("ANTIPHASE", 0.83, 0.18), ("FLOAT", 0.9, 0.62)]:
        axes[2].text(x, y, text, color="white", ha="center", va="center", fontsize=7.5, fontweight="bold")
    figure.suptitle(f"ANNNI ring, N = {summary['qubits']}, exact diagonalisation, p = 0", fontsize=10)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/clean_correlators.png", dpi=200)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    axes[0].imshow(predicted, origin="lower", extent=EXTENT, aspect="auto", cmap=PHASE_COLORS,
                   vmin=0, vmax=3, interpolation="nearest")
    overlay(axes[0])
    frame(axes[0], "Our classifier (unsupervised, 3 clusters)")
    axes[1].imshow(reference, origin="lower", extent=EXTENT, aspect="auto", cmap=PHASE_COLORS,
                   vmin=0, vmax=3, interpolation="nearest")
    overlay(axes[1])
    frame(axes[1], "Analytic reference labels")

    disagreement = (predicted != reference).astype(float)
    floating = (reference == FLOATING)
    axes[2].imshow(disagreement, origin="lower", extent=EXTENT, aspect="auto", cmap="Greys", vmin=0, vmax=1.4)
    axes[2].contour(np.linspace(0, 1, floating.shape[1]), np.linspace(0, 2, floating.shape[0]),
                    floating.astype(float), levels=[0.5], colors=[BLUE], linewidths=1.2)
    overlay(axes[2], color=ORANGE, linewidth=1.0)
    frame(axes[2], "Disagreement (black) - blue outline: floating band")
    accuracy_text = (f"cell accuracy excluding floating cells: {summary['accuracy_excluding_floating']:.1%}"
                     f"   |   all cells: {summary['accuracy_all_cells']:.1%}")
    figure.suptitle(accuracy_text, fontsize=10)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/clean_phase_diagram.png", dpi=200)
    plt.close(figure)
    print("wrote figures/clean_correlators.png and figures/clean_phase_diagram.png")


if __name__ == "__main__":
    main()
