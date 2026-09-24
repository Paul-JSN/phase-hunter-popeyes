"""Build the demo's archived clean / noisy / corrected comparison.

Run ``python3 scripts/make_comparison.py``; only NumPy is required. No circuit is
refit. Maps use the exponential two-point estimator from second_method.py.
The finite-shot experiment uses *linear* extrapolation: exponentiating a noisy
ratio is unstable near zero. All comparisons target the SAME circuit at p=0,
not the exact ground state or the thermodynamic phase diagram.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.classify import ORDER, fit_centroids
from src.reference import ANTIPHASE, FERRO, PARA

LOW, HIGH = 0.01, 0.05
DEFAULT_SEED = 20260923
PHASE_KEYS = {FERRO: "ferro", ANTIPHASE: "antiphase", PARA: "paramagnetic"}


def exponential_extrapolation(a, b):
    """Match the archived infinite-shot two-point correction exactly."""
    linear = (HIGH * a - LOW * b) / (HIGH - LOW)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(np.abs(b) > 1e-6, np.abs(a) / np.abs(b), np.nan)
        rate = np.log(np.clip(ratio, 1e-9, None)) / (HIGH - LOW)
        exponential = np.sign(a) * np.abs(a) * np.exp(rate * LOW)
    return np.where(np.isfinite(exponential), exponential, linear)


def linear_extrapolation(a, b):
    """Unclipped Richardson estimate; values outside [-1, 1] are allowed."""
    return (HIGH * a - LOW * b) / (HIGH - LOW)


def classify_features(features, centroids):
    return np.asarray(ORDER)[np.argmin(
        np.sum((features[..., None, :] - centroids) ** 2, axis=-1), axis=-1)]


def summary(values):
    return {"mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)),
            "se": float(np.std(values, ddof=1) / np.sqrt(len(values)))}


def paired_summary(values):
    result = summary(values)
    result["ci95"] = [result["mean"] - 1.96 * result["se"],
                      result["mean"] + 1.96 * result["se"]]
    return result


def draw_joint_means(rng, probabilities, outcomes, shots):
    """One full-register Z shot gives BOTH correlators; keep their covariance."""
    counts = rng.multinomial(shots, probabilities)
    return counts @ outcomes / shots


def finite_shot_experiment(probabilities, outcomes, truth, clean_labels, centroids,
                           budgets=(20, 100, 500), repeats=200, seed=DEFAULT_SEED):
    """Equal per-cell shot cost, independent full maps over seeded repetitions.

    Couple protocols by sharing first half-batches for paired differences:
    noisy uses both p=.05 halves, low_noise both p=.01 halves, and corrected
    uses one half of each. Each arm still has exactly B shots per point.
    """
    if repeats < 2 or any(b < 2 or b % 2 for b in budgets):
        raise ValueError("Use at least two repeats and positive even shot budgets.")
    results = []
    streams = np.random.SeedSequence(seed).spawn(len(budgets))
    for budget, budget_stream in zip(budgets, streams):
        metrics = {name: {"mae": [], "agreement": []}
                   for name in ("noisy", "low_noise", "corrected")}
        for repeat_stream in budget_stream.spawn(repeats):
            rng = np.random.default_rng(repeat_stream)
            low1 = draw_joint_means(rng, probabilities[0], outcomes, budget // 2)
            low2 = draw_joint_means(rng, probabilities[0], outcomes, budget // 2)
            high1 = draw_joint_means(rng, probabilities[1], outcomes, budget // 2)
            high2 = draw_joint_means(rng, probabilities[1], outcomes, budget // 2)
            arms = {"noisy": (high1 + high2) / 2,
                    "low_noise": (low1 + low2) / 2,
                    "corrected": linear_extrapolation(low1, high1)}
            for name, estimate in arms.items():
                metrics[name]["mae"].append(float(np.abs(estimate - truth).mean()))
                metrics[name]["agreement"].append(float(np.mean(
                    classify_features(estimate, centroids) == clean_labels)))
        row = {"shots": int(budget), "total_shots_per_map": int(budget * len(truth))}
        for name, values in metrics.items():
            mae, agreement = summary(values["mae"]), summary(values["agreement"])
            row[name] = {"mae": mae["mean"], "mae_sd": mae["sd"], "mae_se": mae["se"],
                         "agreement": agreement["mean"], "agreement_sd": agreement["sd"],
                         "agreement_se": agreement["se"]}
        # Positive improvement means correction lowers error / raises agreement.
        row["paired_mae_improvement"] = {
            "vs_" + name: paired_summary(np.array(metrics[name]["mae"]) -
                                         metrics["corrected"]["mae"])
            for name in ("noisy", "low_noise")}
        row["paired_agreement_improvement"] = {
            "vs_" + name: paired_summary(np.array(metrics["corrected"]["agreement"]) -
                                         metrics[name]["agreement"])
            for name in ("noisy", "low_noise")}
        results.append(row)
    return {
        "protocol": "Whole-register Z readout; C1 and C2 are estimated jointly from every shot. "
                    "Each arm uses the same total B shots per grid point: noisy has B at p=0.05; "
                    "low_noise has B at p=0.01; corrected splits B/2 at each level. "
                    "Fixed clean centroids; errors and label agreement target the same p=0 circuit.",
        "method": "Linear two-point extrapolation (1.25 × low-noise − 0.25 × noisy), unclipped",
        "budgets": list(budgets), "seeds": repeats, "seed": seed, "points": len(truth),
        "grid_selection": "All 24 × 24 archived points, chosen before sampling; no point selection.",
        "pairing": "The two baseline arms each combine two independent B/2 batches. Correction "
                   "reuses the first low and high batches, preserving each arm's B-shot "
                   "marginal distribution while allowing paired comparisons.",
        "results": results,
        "uncertainties": [
            "SD is run-to-run variation over independent seeded full-grid repetitions; "
            "SE describes Monte Carlo uncertainty in the reported mean.",
            "Paired 95% intervals are mean ± 1.96 SE. They describe sampling repeatability "
            "for this fixed circuit/grid, not uncertainty in the noise model or a phase boundary.",
            "The p=0 reference and clean centroids are taken as known; calibration/preparation "
            "cost is excluded. p=0.01 and p=0.05 access is assumed equally costly per shot.",
            "This finite-shot test uses linear correction, unlike the exponential infinite-shot "
            "comparison maps. It is a simulation using recovered joint readout probabilities.",
        ],
    }


def load_validated_archives(root=ROOT):
    archive_path = root / "data/pennylane_scan_N8.npz"
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with np.load(archive_path) as source:
        scan = {key: source[key] for key in source.files}
    with np.load(root / "data/readout_N8.npz") as source:
        readout = {key: source[key] for key in source.files}
    if str(readout["archive_sha256"]) != digest:
        raise ValueError("Readout archive was recovered from a different scan.")
    for axis in ("kappas", "hs", "noise"):
        if not np.array_equal(scan[axis], readout[axis]):
            raise ValueError(f"Readout axis mismatch: {axis}")
    probabilities = readout["readout"]
    if probabilities.shape != (len(scan["noise"]), len(scan["hs"]),
                                len(scan["kappas"]), len(readout["outcomes"])):
        raise ValueError("Readout grid has an unexpected shape.")
    if probabilities.min() < -1e-12 or not np.allclose(probabilities.sum(-1), 1, atol=1e-12):
        raise ValueError("Readout distributions are not normalized probabilities.")
    means = probabilities @ readout["outcomes"]
    max_error = 0.0
    for index, noise in enumerate(scan["noise"]):
        expected = np.stack([scan[f"p{noise}_{key}"] for key in ("zz1", "zz2")], axis=-1)
        max_error = max(max_error, float(np.max(np.abs(means[index] - expected))))
    if max_error > 1e-7:
        raise ValueError(f"Recovered readout does not reproduce the archive: {max_error}")
    return scan, readout, {"archive_sha256": digest,
                           "readout_mean_max_difference": max_error}


def build_report(repeats=200, budgets=(20, 100, 500), seed=DEFAULT_SEED):
    scan, readout, validation = load_validated_archives()
    kappas, hs = scan["kappas"], scan["hs"]
    clean = np.stack([scan[f"p0.0_{key}"] for key in ("zz1", "zz2")], axis=-1)
    low = np.stack([scan[f"p{LOW}_{key}"] for key in ("zz1", "zz2")], axis=-1)
    noisy = np.stack([scan[f"p{HIGH}_{key}"] for key in ("zz1", "zz2")], axis=-1)
    corrected = exponential_extrapolation(low, noisy)
    centroids = fit_centroids(clean[..., 0], clean[..., 1], kappas, hs)
    clean_labels = classify_features(clean, centroids)
    maps = {}
    for name, features in (("clean", clean), ("noisy", noisy), ("corrected", corrected)):
        labels = classify_features(features, centroids)
        maps[name] = {"labels": labels.tolist(),
                      "ordered_area": float(np.isin(labels, [FERRO, ANTIPHASE]).mean()),
                      "agreement_to_clean": float((labels == clean_labels).mean()),
                      "signal_mae": float(np.abs(features - clean).mean()),
                      "phase_areas": {key: float((labels == phase).mean())
                                      for phase, key in PHASE_KEYS.items()}}
    kgrid, hgrid = np.meshgrid(kappas, hs)
    interiors = []
    for phase, label, observable, index, mask, bounds in (
        (FERRO, "Ferromagnetic", "nearest-neighbour |C1|", 0,
         (kgrid < .3) & (hgrid > .1) & (hgrid < .4), "κ < 0.3, 0.1 < h < 0.4"),
        (ANTIPHASE, "Antiphase", "next-nearest-neighbour |C2|", 1,
         (kgrid > .8) & (hgrid > .1) & (hgrid < .4), "κ > 0.8, 0.1 < h < 0.4"),
    ):
        key = PHASE_KEYS[phase]
        clean_signal = float(np.abs(clean[..., index][mask]).mean())
        noisy_signal = float(np.abs(noisy[..., index][mask]).mean())
        losses = 1 - np.abs(noisy[..., index][mask]) / np.abs(clean[..., index][mask])
        clean_area, noisy_area = [maps[name]["phase_areas"][key] for name in ("clean", "noisy")]
        # Distance to the nearest Voronoi decision plane, positive inside the
        # clean assigned class. This is a geometric classifier margin, not an
        # independent physical order parameter or a causal boundary proof.
        margins = {}
        for name, features in (("clean", clean), ("noisy", noisy)):
            d2 = np.sum((features[..., None, :] - centroids) ** 2, axis=-1)
            own = ORDER.index(phase)
            alternatives = [i for i in range(len(ORDER)) if i != own]
            plane_distances = [(d2[..., j] - d2[..., own]) /
                               (2 * np.linalg.norm(centroids[j] - centroids[own]))
                               for j in alternatives]
            margins[name] = float(np.min(plane_distances, axis=0)[clean_labels == phase].mean())
        interiors.append({"phase": key, "label": label, "observable": observable,
                          "points": int(mask.sum()), "region": bounds,
                          "clean_signal": clean_signal, "noisy_signal": noisy_signal,
                          "signal_loss": 1 - noisy_signal / clean_signal,
                          "point_loss_min": float(losses.min()), "point_loss_max": float(losses.max()),
                          "clean_area": clean_area, "noisy_area": noisy_area,
                          "area_loss": 1 - noisy_area / clean_area,
                          "clean_margin_mean": margins["clean"], "noisy_margin_mean": margins["noisy"]})
    indices = [int(np.flatnonzero(np.isclose(readout["noise"], p))[0]) for p in (LOW, HIGH)]
    probabilities = readout["readout"][indices].reshape(2, -1, len(readout["outcomes"]))
    finite = finite_shot_experiment(probabilities, readout["outcomes"], clean.reshape(-1, 2),
                                    clean_labels.ravel(), centroids, budgets, repeats, seed)
    return {
        "version": 1, "kappas": kappas.tolist(), "hs": hs.tolist(), "maps": maps,
        "interiors": interiors, "finite_shots": finite,
        "metadata": {
            "qubits": 8, "grid": [len(hs), len(kappas)],
            "sources": ["data/pennylane_scan_N8.npz", "data/readout_N8.npz"],
            "phase_codes": {str(phase): key for phase, key in PHASE_KEYS.items()},
            "centroid_order": ORDER, "centroids": centroids.tolist(),
            "clean": "p=0 expectations of the archived variational circuit; not an exact ground state.",
            "noisy": "The same circuit with gate depolarizing probability p=0.05.",
            "corrected": "Two-point exponential extrapolation from p=0.01 and p=0.05 "
                         "expectations, with the same linear fallback as scripts/second_method.py.",
            "exponential_diagnostics": {
                "near_zero_high_noise_observables": int(np.sum(np.abs(noisy) <= 1e-6)),
                "sign_changes_between_noise_levels": int(np.sum(low * noisy < 0)),
                "note": "The archived estimator takes absolute ratios even when small signals "
                        "change sign; these cases weaken an exponential-decay interpretation. "
                        "The finite-shot test therefore uses a linear estimator.",
            },
            "classification": "Fit three correlator-space centroids once on p=0, then freeze them "
                              "for every map and sampled run. Floating phase is not resolved.",
            "metrics": "Agreement is fraction of cells matching the p=0 labels. Signal MAE averages "
                       "absolute error in C1 and C2 against the same p=0 circuit, over all cells.",
            "interpretation": "Signal decay and classified area measure different things. Gate noise "
                              "attenuates correlators differently; the frozen classifier also depends "
                              "on both correlators and their distance to its decision planes. "
                              "Changing label area is not proof of a changed physical transition.",
            "interior_sampling": "Signal loss is computed from means over predefined interior patches, "
                                 "not a single point. Area loss is relative to the clean classified area "
                                 "over the whole grid; margin means use the clean-labelled cells.",
            "limitations": "Archived classical circuit simulation, N=8, a 24×24 grid and one noise "
                           "model. The maps use infinite-shot expectations; finite-shot results "
                           "below use linear rather than exponential extrapolation.",
            "validation": validation,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    report = build_report(repeats=args.repeats, seed=args.seed)
    (ROOT / "data/comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (ROOT / "game/comparison-data.js").write_text(
        "// Generated by scripts/make_comparison.py; do not edit by hand.\n" +
        "window.PHASE_COMPARISON = " + json.dumps(report, separators=(",", ":"), allow_nan=False) + ";\n")
    print(json.dumps({"maps": {key: {k: v for k, v in row.items() if k != "labels"}
                              for key, row in report["maps"].items()},
                      "interiors": report["interiors"],
                      "finite_shots": report["finite_shots"]["results"]}, indent=2))


if __name__ == "__main__":
    main()
