"""Two independent checks on the main result.

    python3 scripts/second_method.py

1. Fidelity susceptibility. A method that shares nothing with the clustering:
   take the overlap between ground states at neighbouring field values and look
   for where it drops. Peaks mark transitions. If this agrees with the
   correlator clustering, two unrelated methods are pointing at the same lines.

2. Zero-noise extrapolation. We have correlators at p = 0.01 and p = 0.05, so we
   can extrapolate each one back to p = 0 and compare with the clean data we
   already hold. That both tests the multiplicative-attenuation claim the main
   result rests on, and is the challenge's error-mitigation bonus.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.annni import AnnniChain
from src.classify import assign, classify, fit_centroids
from src.reference import (ANTIPHASE, FERRO, FLOATING, bkt_transition, ising_transition,
                           kt_transition, reference_labels)

TEAL, ORANGE, PURPLE, BLUE, NAVY, MUTED, LINE = ("#007F7A", "#D4742B", "#7356A6", "#377CA8",
                                                 "#152638", "#546573", "#DCE4E7")
plt.rcParams.update({"font.size": 9, "axes.edgecolor": LINE, "axes.labelcolor": NAVY,
                     "text.color": NAVY, "xtick.color": MUTED, "ytick.color": MUTED})


def overlay(axis, color="white", lw=1.4):
    left, right = np.linspace(0.001, 0.499, 200), np.linspace(0.5, 1, 200)
    axis.plot(left, ising_transition(left), color=color, lw=lw)
    axis.plot(right, bkt_transition(right), color=color, lw=lw, ls="--")
    axis.plot(right, kt_transition(right), color=color, lw=lw, ls=":")


def degenerate_subspace(chain, kappa, h, tol=1e-3):
    """The ground manifold, not just one vector.

    On a finite ring the ordered phases have quasi-degenerate ground states (a
    spin-flip doublet in the ferromagnet, a translation quartet in the antiphase)
    and at h = 0 they are exactly degenerate. `eigh` then hands back an arbitrary
    basis of that manifold, so the overlap of two neighbouring *vectors* is
    meaningless. Comparing the whole manifold instead is gauge invariant.
    """
    values, vectors = np.linalg.eigh(chain.hamiltonian(kappa, h))
    size = int(np.sum(values - values[0] < tol))
    return vectors[:, :size]


def subspace_fidelity(lo, hi):
    """Product of the singular values of the overlap: 1 if the manifolds coincide."""
    size = min(lo.shape[1], hi.shape[1])
    singular = np.linalg.svd(lo[:, :size].conj().T @ hi[:, :size], compute_uv=False)
    return float(np.prod(np.clip(singular, 0, 1)))


def fidelity_susceptibility(n_qubits=8, grid=40):
    """chi_F(kappa, h) from the overlap of neighbouring ground manifolds in h."""
    chain = AnnniChain(n_qubits)
    kappas = np.linspace(0, 1, grid)
    hs = np.linspace(0, 2, grid)
    dh = hs[1] - hs[0]
    chi = np.zeros((grid, grid))
    for b, kappa in enumerate(kappas):
        manifolds = [degenerate_subspace(chain, float(kappa), float(h)) for h in hs]
        for a in range(grid):
            below, above = max(a - 1, 0), min(a + 1, grid - 1)
            step = dh * (above - below)
            chi[a, b] = 2 * (1 - subspace_fidelity(manifolds[below], manifolds[above])) / step ** 2
    return kappas, hs, chi


def peak_positions(kappas, hs, chi):
    """For each kappa column, the field at which chi_F peaks."""
    return np.array([hs[int(np.argmax(chi[:, b]))] for b in range(len(kappas))])


def main() -> None:
    report = {}

    # ---------------- 1. fidelity susceptibility ----------------
    kappas, hs, chi = fidelity_susceptibility()
    peaks = peak_positions(kappas, hs, chi)
    analytic = np.where(kappas < 0.5, ising_transition(np.maximum(kappas, 1e-4)),
                        kt_transition(np.maximum(kappas, 0.5001)))
    usable = (kappas > 0.05) & (kappas < 0.95) & np.isfinite(analytic)
    deviation = np.abs(peaks - analytic)[usable]

    clean = AnnniChain(8).grid(kappas, hs)
    labels = classify(clean["zz1"], clean["zz2"], kappas, hs)
    ordered = np.isin(labels, [FERRO, ANTIPHASE])
    cluster_edge = np.array([hs[np.where(ordered[:, b])[0].max()] if ordered[:, b].any() else np.nan
                             for b in range(len(kappas))])
    between = np.abs(peaks - cluster_edge)[usable & np.isfinite(cluster_edge)]

    # the floating corner is where every method in this project struggles, so split it out
    away = (kappas > 0.05) & (kappas <= 0.85)
    corner = (kappas > 0.85) & (kappas < 0.95)
    report["fidelity_susceptibility"] = {
        "mean_abs_deviation_from_analytic": float(deviation.mean()),
        "median_abs_deviation_from_analytic": float(np.median(deviation)),
        "mean_abs_deviation_kappa_below_0.85": float(np.abs(peaks - analytic)[away].mean()),
        "mean_abs_deviation_kappa_above_0.85": float(np.abs(peaks - analytic)[corner].mean()),
        "mean_abs_gap_to_clustering": float(between.mean()),
        "grid_spacing_in_h": float(hs[1] - hs[0]),
    }
    print("fidelity susceptibility vs analytic lines: "
          f"mean |Δh| = {deviation.mean():.3f} (grid spacing {hs[1]-hs[0]:.3f}); "
          f"kappa<=0.85 {np.abs(peaks - analytic)[away].mean():.3f}, "
          f"kappa>0.85 {np.abs(peaks - analytic)[corner].mean():.3f}")
    print(f"fidelity susceptibility vs our clustering: mean |Δh| = {between.mean():.3f}")

    # ---------------- 2. zero-noise extrapolation ----------------
    scan = np.load(ROOT / "data/pennylane_scan_N8.npz")
    truth = {k: scan[f"p0.0_{k}"] for k in ("zz1", "zz2")}
    p1, p2 = 0.01, 0.05
    mitigated, before, after = {}, {}, {}
    for key in ("zz1", "zz2"):
        a, b = scan[f"p{p1}_{key}"], scan[f"p{p2}_{key}"]
        linear = (p2 * a - p1 * b) / (p2 - p1)                       # Richardson, first order
        with np.errstate(divide="ignore", invalid="ignore"):         # exponential, two-point fit
            ratio = np.where(np.abs(b) > 1e-6, np.abs(a) / np.abs(b), np.nan)
            rate = np.log(np.clip(ratio, 1e-9, None)) / (p2 - p1)
            exponential = np.sign(a) * np.abs(a) * np.exp(rate * p1)
        exponential = np.where(np.isfinite(exponential), exponential, linear)
        mitigated[key] = {"linear": linear, "exponential": exponential}
        before[key] = float(np.abs(b - truth[key]).mean())
        after[key] = {"linear": float(np.abs(linear - truth[key]).mean()),
                      "exponential": float(np.abs(exponential - truth[key]).mean())}
        print(f"{key}: |noisy(p=0.05) - clean| = {before[key]:.4f}   "
              f"linear {after[key]['linear']:.4f}   exponential {after[key]['exponential']:.4f}")

    reference = reference_labels(*np.meshgrid(scan["kappas"], scan["hs"]))
    detectable = reference != FLOATING
    centroids = fit_centroids(truth["zz1"], truth["zz2"], scan["kappas"], scan["hs"])
    areas = {}
    for name, z1, z2 in [("clean", truth["zz1"], truth["zz2"]),
                         ("noisy p=0.05", scan["p0.05_zz1"], scan["p0.05_zz2"]),
                         ("mitigated (linear)", mitigated["zz1"]["linear"], mitigated["zz2"]["linear"]),
                         ("mitigated (exponential)", mitigated["zz1"]["exponential"], mitigated["zz2"]["exponential"])]:
        fixed = assign(z1, z2, centroids)
        areas[name] = {"ordered_area": float(np.isin(fixed, [FERRO, ANTIPHASE]).mean()),
                       "agreement": float((fixed[detectable] == reference[detectable]).mean())}
        print(f"{name:26} ordered area {areas[name]['ordered_area']:6.1%}   "
              f"agreement {areas[name]['agreement']:6.1%}")
    report["zero_noise_extrapolation"] = {"mean_abs_error_before": before, "mean_abs_error_after": after,
                                          "phase_areas_under_the_clean_rule": areas}
    (ROOT / "data/second_method.json").write_text(json.dumps(report, indent=2))

    # ---------------- figures ----------------
    figure, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    image = axes[0].imshow(np.log10(np.clip(chi, 1e-3, None)), origin="lower", extent=[0, 1, 0, 2],
                           aspect="auto", cmap="magma")
    figure.colorbar(image, ax=axes[0], shrink=.85, label=r"$\log_{10}\chi_F$")
    overlay(axes[0], "white")
    axes[0].set(xlabel=r"$\kappa$", ylabel="$h$", title="Fidelity susceptibility (independent method)")

    axes[1].plot(kappas[usable], peaks[usable], "o-", color=TEAL, lw=2, ms=3.5, label="χ$_F$ peak")
    axes[1].plot(kappas[usable], cluster_edge[usable], "s--", color=PURPLE, lw=1.8, ms=3, label="our clustering")
    axes[1].plot(kappas[usable], analytic[usable], color=NAVY, lw=1.6, label="analytic")
    axes[1].set(xlabel=r"$\kappa$", ylabel="$h$ of the boundary", title="Three ways to find the same line")
    axes[1].legend(frameon=False, fontsize=8)

    labels_plot = ["noisy\np=0.05", "linear\nextrapolation", "exponential\nextrapolation"]
    zz1_errors = [before["zz1"], after["zz1"]["linear"], after["zz1"]["exponential"]]
    zz2_errors = [before["zz2"], after["zz2"]["linear"], after["zz2"]["exponential"]]
    x = np.arange(3)
    axes[2].bar(x - 0.18, zz1_errors, 0.34, color=TEAL, label=r"$\langle ZZ\rangle_1$")
    axes[2].bar(x + 0.18, zz2_errors, 0.34, color=PURPLE, label=r"$\langle ZZ\rangle_2$")
    axes[2].set_xticks(x); axes[2].set_xticklabels(labels_plot, fontsize=8)
    axes[2].set(ylabel="mean |error| vs clean data", title="Zero-noise extrapolation")
    axes[2].legend(frameon=False, fontsize=8)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/second_method.png", dpi=200)
    print("\nwrote figures/second_method.png and data/second_method.json")


if __name__ == "__main__":
    main()
