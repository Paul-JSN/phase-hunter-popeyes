"""Turn the PennyLane scan into the submitted phase diagrams and noise analysis.

    python3 scripts/analyse_noise.py [--qubits 8]

Two classifications are produced at every noise level:

  fixed  - cluster centres fitted once on the p = 0 data and then applied
           unchanged. This is what happens when a classifier is calibrated on
           clean simulations and pointed at noisy hardware.
  recal  - centres re-fitted on the noisy data itself.

The gap between them is the result: depolarizing noise attenuates correlators
nearly multiplicatively, so a fixed rule reports the ordered phases shrinking
while a recalibrated one still finds the boundaries.
"""
from __future__ import annotations

import argparse
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

from src.classify import assign, classify, fit_centroids
from src.reference import (ANTIPHASE, FERRO, FLOATING, PARA, bkt_transition, ising_transition,
                           kt_transition, reference_labels)

TEAL, ORANGE, PURPLE, BLUE = "#007F7A", "#D4742B", "#7356A6", "#377CA8"
NAVY, MUTED, LINE = "#152638", "#546573", "#DCE4E7"
PHASES = ListedColormap([TEAL, ORANGE, PURPLE, BLUE])
EXTENT = [0, 1, 0, 2]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": LINE, "axes.labelcolor": NAVY,
                     "text.color": NAVY, "xtick.color": MUTED, "ytick.color": MUTED,
                     "figure.facecolor": "white"})


def overlay(axis, color="white", lw=1.4):
    left, right = np.linspace(0.001, 0.499, 200), np.linspace(0.5, 1, 200)
    axis.plot(left, ising_transition(left), color=color, lw=lw)
    axis.plot(right, bkt_transition(right), color=color, lw=lw, ls="--")
    axis.plot(right, kt_transition(right), color=color, lw=lw, ls=":")


def frame(axis, title):
    axis.set_xlim(0, 1); axis.set_ylim(0, 2)
    axis.set_xlabel(r"$\kappa$"); axis.set_ylabel(r"$h$")
    axis.set_title(title, fontsize=9.5)


def boundary(labels, hs, column, phase):
    rows = np.where(labels[:, column] == phase)[0]
    return float(hs[rows.max()]) if len(rows) else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=8)
    arguments = parser.parse_args()

    data = np.load(ROOT / f"data/pennylane_scan_N{arguments.qubits}.npz")
    kappas, hs = data["kappas"], data["hs"]
    noises = [float(p) for p in data["noise"]]
    reference = reference_labels(*np.meshgrid(kappas, hs))
    detectable = reference != FLOATING

    centroids = fit_centroids(data["p0.0_zz1"], data["p0.0_zz2"], kappas, hs)
    fixed, recal, areas = {}, {}, {}
    for p in noises:
        zz1, zz2 = data[f"p{p}_zz1"], data[f"p{p}_zz2"]
        fixed[p] = assign(zz1, zz2, centroids)
        recal[p] = classify(zz1, zz2, kappas, hs)
        areas[p] = {
            "fixed_rule": {
                "ordered": float(np.isin(fixed[p], [FERRO, ANTIPHASE]).mean()),
                "ferro": float((fixed[p] == FERRO).mean()),
                "antiphase": float((fixed[p] == ANTIPHASE).mean()),
                "agreement": float((fixed[p][detectable] == reference[detectable]).mean())},
            "recalibrated": {
                "ordered": float(np.isin(recal[p], [FERRO, ANTIPHASE]).mean()),
                "agreement": float((recal[p][detectable] == reference[detectable]).mean())},
        }

    # order parameter decay deep inside each region
    kappa_grid, h_grid = np.meshgrid(kappas, hs)
    regions = {
        "ferromagnetic": ((kappa_grid < 0.3) & (h_grid > 0.1) & (h_grid < 0.4), "zz1"),
        "antiphase": ((kappa_grid > 0.8) & (h_grid > 0.1) & (h_grid < 0.4), "zz2"),
        "paramagnetic": ((h_grid > 1.6), "zz1"),
    }
    decay = {}
    for name, (mask, key) in regions.items():
        clean = float(np.abs(data[f"p0.0_{key}"][mask]).mean())
        decay[name] = {"observable": "ZZ(1)" if key == "zz1" else "ZZ(2)", "p0": clean}
        for p in noises:
            if p > 0:
                value = float(np.abs(data[f"p{p}_{key}"][mask]).mean())
                decay[name][f"p{p}"] = value
                decay[name][f"relative_loss_p{p}"] = float(1 - value / clean)

    cuts = {}
    for kappa_value, phase in ((0.20, FERRO), (0.30, FERRO), (0.90, ANTIPHASE)):
        column = int(np.argmin(np.abs(kappas - kappa_value)))
        analytic = (float(ising_transition(np.array([kappas[column]]))[0]) if kappas[column] < 0.5
                    else float(kt_transition(np.array([kappas[column]]))[0]))
        cuts[f"kappa={kappas[column]:.2f}"] = {
            "phase": "ferro" if phase == FERRO else "antiphase", "analytic_boundary": analytic,
            **{f"fixed_p{p}": boundary(fixed[p], hs, column, phase) for p in noises},
            **{f"recal_p{p}": boundary(recal[p], hs, column, phase) for p in noises}}

    # figure: fixed rule (top) and recalibrated (bottom)
    figure, axes = plt.subplots(2, len(noises), figsize=(3.7 * len(noises), 7.0))
    for column, p in enumerate(noises):
        for row, (labels, tag) in enumerate(((fixed, "calibrated at p = 0"), (recal, "recalibrated"))):
            axis = axes[row, column]
            axis.imshow(labels[p], origin="lower", extent=EXTENT, aspect="auto", cmap=PHASES,
                        vmin=0, vmax=3, interpolation="nearest")
            overlay(axis)
            ordered = np.isin(labels[p], [FERRO, ANTIPHASE]).mean()
            frame(axis, f"p = {p}, {tag}\nordered area {ordered:.1%}")
    figure.suptitle(f"ANNNI phase diagram under depolarizing noise (N = {arguments.qubits}, "
                    f"{len(kappas)}x{len(hs)} grid, VQE state preparation)", fontsize=10.5)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/phase_diagrams_noise.png", dpi=200)
    plt.close(figure)

    # figure: decay and shrinkage
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.4))
    colors = {"ferromagnetic": TEAL, "antiphase": PURPLE, "paramagnetic": ORANGE}
    for name, row in decay.items():
        axes[0].plot(noises, [row["p0"]] + [row[f"p{p}"] for p in noises if p > 0], "o-",
                     color=colors[name], lw=2, label=name)
        axes[1].plot([p for p in noises if p > 0],
                     [100 * row[f"relative_loss_p{p}"] for p in noises if p > 0], "o-",
                     color=colors[name], lw=2, label=name)
    axes[0].set(xlabel="depolarizing probability p", ylabel="|order parameter|",
                title="Order parameter vs noise")
    axes[1].set(xlabel="depolarizing probability p", ylabel="relative loss (%)",
                title="Fractional loss")
    for axis in axes[:2]:
        axis.legend(frameon=False, fontsize=8)
    axes[2].plot(noises, [100 * areas[p]["fixed_rule"]["ordered"] for p in noises], "o-",
                 color=NAVY, lw=2, label="rule calibrated at p = 0")
    axes[2].plot(noises, [100 * areas[p]["recalibrated"]["ordered"] for p in noises], "o--",
                 color=BLUE, lw=2, label="rule recalibrated")
    axes[2].set(xlabel="depolarizing probability p", ylabel="ordered area (% of plane)",
                title="Apparent size of the ordered phases")
    axes[2].legend(frameon=False, fontsize=8)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/noise_analysis.png", dpi=200)
    plt.close(figure)

    report = {
        "qubits": arguments.qubits, "grid": [len(kappas), len(hs)], "noise_levels": noises,
        "phase_areas": areas, "order_parameter_decay": decay, "boundary_cuts": cuts,
        "vqe_quality": {
            "energy_error_mean": float(np.abs(data["energy_vqe"] - data["energy_exact"]).mean()),
            "energy_error_max": float(np.abs(data["energy_vqe"] - data["energy_exact"]).max()),
            "energy_error_relative_mean": float(np.abs((data["energy_vqe"] - data["energy_exact"])
                                                       / data["energy_exact"]).mean()),
            "zz1_vs_exact_mean_abs": float(np.abs(data["p0.0_zz1"] - data["exact_zz1"]).mean()),
            "zz2_vs_exact_mean_abs": float(np.abs(data["p0.0_zz2"] - data["exact_zz2"]).mean()),
            "refit_fraction": float(data["refits"].mean())},
    }
    (ROOT / "data/noise_analysis.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"phase_areas": areas, "order_parameter_decay": decay,
                      "boundary_cuts": cuts}, indent=2)[:2000])


if __name__ == "__main__":
    main()
