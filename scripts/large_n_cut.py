"""Does the noise conclusion survive at N = 12? A cut instead of a full scan.

    uv run --project "Scientific Track" python scripts/large_n_cut.py --qubits 12

A full 24 x 24 noisy scan at N = 12 is out of reach: the density matrix is
4096 x 4096 and every point needs its own variational fit.  A *cut* is not.
Two vertical lines through the plane -- one crossing the ferromagnet-to-
paramagnet boundary, one crossing the antiphase-to-paramagnet boundary -- are
test a narrower, observable-level question:

    at N = 12, how closely does a scalar attenuation describe the signal,
    and how much does rescaling recover a classifier threshold crossing?

The p = 0 point is evaluated on default.qubit rather than default.mixed: with
no channel the two are the same state, and the state-vector device is far
cheaper.  Everything else runs on default.mixed with a depolarizing channel
after every CNOT, exactly as the N = 8 scan does.

Results are appended to data/large_n_cut.json after every point, so an
interrupted run keeps what it has.  Re-running resumes from the file.

Analysis and figure only, from an existing file (no PennyLane needed):

    python3 scripts/large_n_cut.py --analyse-only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.annni import AnnniChain
from src.reference import ising_transition, kt_transition

OUT = ROOT / "data/large_n_cut.json"
THRESHOLD = 0.46          # the same order-parameter threshold budget_study.py uses
TEAL, ORANGE, PURPLE, NAVY, MUTED, LINE = ("#007F7A", "#D4742B", "#7356A6", "#152638", "#546573", "#DCE4E7")
CUTS = [{"name": "ferromagnet to paramagnet", "kappa": 0.2, "order": "zz1"},
        {"name": "antiphase to paramagnet", "kappa": 0.8, "order": "zz2"}]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": LINE, "axes.labelcolor": NAVY,
                     "text.color": NAVY, "xtick.color": MUTED, "ytick.color": MUTED})


# ---------------------------------------------------------------- measurement

def run(arguments) -> dict:
    from src.pennylane_pipeline import correlators_from_state, noisy_correlators, vqe_ground_state
    import pennylane as qml

    device = qml.device("default.qubit", wires=arguments.qubits)

    def prepared_correlators(params):
        """<ZZ>_1 and <ZZ>_2 of the prepared state, no channel: p = 0 without the density matrix."""
        from src.pennylane_pipeline import ansatz

        @qml.qnode(device)
        def circuit():
            ansatz(params, arguments.qubits, arguments.layers)
            return qml.state()

        return correlators_from_state(np.asarray(circuit()), arguments.qubits)

    record = json.loads(OUT.read_text()) if OUT.exists() else {"qubits": arguments.qubits,
                                                               "layers": arguments.layers,
                                                               "noise_levels": arguments.noise_levels,
                                                               "cuts": {}}
    if record["qubits"] != arguments.qubits:
        raise SystemExit(f"{OUT} holds N = {record['qubits']}; delete it or pass --qubits {record['qubits']}")

    chain = AnnniChain(arguments.qubits)
    hs = np.linspace(arguments.h_min, arguments.h_max, arguments.points)
    started, done, total = time.time(), 0, len(CUTS) * len(hs)

    for cut in CUTS:
        rows = record["cuts"].setdefault(cut["name"], [])
        seen = {round(r["h"], 6) for r in rows}
        warm = None
        for h in hs:
            done += 1
            if round(float(h), 6) in seen:
                continue
            exact_energy = chain.ground_state(cut["kappa"], float(h))[1]
            params, energy = vqe_ground_state(arguments.qubits, cut["kappa"], float(h),
                                              layers=arguments.layers, steps=arguments.steps, init=warm)
            refit = False
            if abs(energy - exact_energy) > arguments.tolerance * abs(exact_energy):
                params, energy = vqe_ground_state(arguments.qubits, cut["kappa"], float(h),
                                                  layers=arguments.layers, steps=arguments.steps * 2)
                refit = True
            warm = np.array(params)

            zz1, zz2 = prepared_correlators(params)
            row = {"h": float(h), "energy": energy, "exact_energy": exact_energy, "refit": refit,
                   "p0.0": {"zz1": zz1, "zz2": zz2}}
            for p in arguments.noise_levels:
                if p == 0.0:
                    continue
                n1, n2 = noisy_correlators(params, arguments.qubits, p, layers=arguments.layers)
                row[f"p{p}"] = {"zz1": n1, "zz2": n2}
            rows.append(row)
            rows.sort(key=lambda r: r["h"])
            OUT.write_text(json.dumps(record, indent=2))

            each = (time.time() - started) / max(done, 1)
            print(f"  {cut['name']:<26} h = {h:4.2f}  dE = {abs(energy - exact_energy):.3f}"
                  f"{'  (refit)' if refit else '        '}  "
                  f"{done}/{total}  eta {(total - done) * each / 60:5.1f} min", flush=True)
    return record


# ------------------------------------------------------------------- analysis

def crossing(hs, values, level):
    """The h at which a falling curve first drops through `level`, linearly interpolated."""
    for i in range(len(hs) - 1):
        if values[i] >= level > values[i + 1]:
            span = values[i] - values[i + 1]
            return float(hs[i] + (hs[i + 1] - hs[i]) * (values[i] - level) / span) if span else float(hs[i])
    return float("nan")


def analyse(record) -> dict:
    rows_all = [row for cut in CUTS for row in record["cuts"][cut["name"]]]
    errors = np.array([abs(row["energy"] - row["exact_energy"]) for row in rows_all])
    hs_first = np.array([row["h"] for row in record["cuts"][CUTS[0]["name"]]])
    report = {"qubits": record["qubits"], "points": len(rows_all),
              "h_spacing": float(np.diff(hs_first).mean()),
              "preparation_energy_error": {"mean": float(errors.mean()), "max": float(errors.max())},
              "cuts": {}}
    for cut in CUTS:
        rows = record["cuts"].get(cut["name"], [])
        if len(rows) < 3:
            continue
        hs = np.array([r["h"] for r in rows])
        clean = np.abs([r["p0.0"][cut["order"]] for r in rows])
        entry = {"kappa": cut["kappa"], "order_parameter": cut["order"],
                 "analytic_boundary": float(ising_transition(cut["kappa"]) if cut["kappa"] < 0.5
                                            else kt_transition(cut["kappa"])),
                 "crossing_clean": crossing(hs, clean, THRESHOLD), "noise": {}}
        for key in (k for k in rows[0] if k.startswith("p") and k != "p0.0"):
            noisy = np.abs([r[key][cut["order"]] for r in rows])
            # one scalar attenuation factor for the whole cut: the claim under test
            factor = float(clean @ noisy / (clean @ clean)) if clean @ clean else float("nan")
            residual = float(np.abs(noisy - factor * clean).mean())
            entry["noise"][key] = {
                "attenuation_factor": factor,
                "mean_residual_after_rescaling": residual,
                "crossing_fixed_threshold": crossing(hs, noisy, THRESHOLD),
                "crossing_rescaled_threshold": crossing(hs, noisy, THRESHOLD * factor),
            }
            entry["noise"][key]["shift_fixed"] = entry["noise"][key]["crossing_fixed_threshold"] - entry["crossing_clean"]
            entry["noise"][key]["shift_rescaled"] = entry["noise"][key]["crossing_rescaled_threshold"] - entry["crossing_clean"]
        report["cuts"][cut["name"]] = entry
    return report


def draw(record, report) -> None:
    figure, axes = plt.subplots(1, len(CUTS), figsize=(11, 3.8))
    colors = {"p0.01": ORANGE, "p0.05": PURPLE}
    for axis, cut in zip(np.atleast_1d(axes), CUTS):
        rows = record["cuts"].get(cut["name"], [])
        if len(rows) < 3:
            continue
        entry = report["cuts"][cut["name"]]
        hs = np.array([r["h"] for r in rows])
        clean = np.abs([r["p0.0"][cut["order"]] for r in rows])
        axis.plot(hs, clean, "o-", color=TEAL, lw=2, ms=4, label="p = 0")
        axis.axhline(THRESHOLD, color=NAVY, lw=1, ls="--")
        for key, values in entry["noise"].items():
            noisy = np.abs([r[key][cut["order"]] for r in rows])
            color = colors.get(key, MUTED)
            axis.plot(hs, noisy, "o-", color=color, lw=1.8, ms=3.5, label=f"p = {key[1:]}")
            axis.axhline(THRESHOLD * values["attenuation_factor"], color=color, lw=0.9, ls=":")
        axis.axvline(entry["analytic_boundary"], color=MUTED, lw=1, label="analytic reference")
        label = r"$|\langle ZZ\rangle_1|$" if cut["order"] == "zz1" else r"$|\langle ZZ\rangle_2|$"
        axis.set(xlabel="$h$", ylabel=label,
                 title=f"{cut['name']}  ($\\kappa$ = {cut['kappa']}, N = {record['qubits']})")
        axis.legend(frameon=False, fontsize=8)
    figure.tight_layout()
    figure.savefig(ROOT / "figures/large_n_cut.png", dpi=200)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=12, help="multiples of four accommodate an unfrustrated period-four stripe")
    parser.add_argument("--points", type=int, default=9)
    parser.add_argument("--h-min", type=float, default=0.1)
    parser.add_argument("--h-max", type=float, default=1.3)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--tolerance", type=float, default=0.03, help="relative energy error before a cold refit")
    parser.add_argument("--noise-levels", type=float, nargs="+", default=[0.01, 0.05])
    parser.add_argument("--analyse-only", action="store_true")
    arguments = parser.parse_args()

    if arguments.qubits % 4:
        print(f"N = {arguments.qubits} is not divisible by four; interpret the stripe cut as a frustrated finite ring.")

    record = json.loads(OUT.read_text()) if arguments.analyse_only else run(arguments)
    expected_hs = np.linspace(arguments.h_min, arguments.h_max, arguments.points)
    for cut in CUTS:
        hs = np.array([row["h"] for row in record["cuts"].get(cut["name"], [])])
        if hs.shape != expected_hs.shape or not np.allclose(hs, expected_hs):
            raise SystemExit(f"Incomplete or unexpected cut: {cut['name']}. Expected {arguments.points} points; pass the matching grid arguments for a non-default scan.")
    report = analyse(record)
    def json_finite(value):
        if isinstance(value, dict): return {key: json_finite(item) for key, item in value.items()}
        if isinstance(value, float) and not np.isfinite(value): return None
        return value
    (ROOT / "data/large_n_cut_analysis.json").write_text(json.dumps(json_finite(report), indent=2, allow_nan=False) + "\n")
    draw(record, report)

    print(f"\nN = {report['qubits']}")
    for name, entry in report["cuts"].items():
        print(f"\n{name}  (kappa = {entry['kappa']}, analytic boundary h = {entry['analytic_boundary']:.2f})")
        print(f"  clean crossing                       h = {entry['crossing_clean']:.3f}")
        for key, values in entry["noise"].items():
            print(f"  {key}: attenuation x{values['attenuation_factor']:.3f} "
                  f"(residual after rescaling {values['mean_residual_after_rescaling']:.4f})")
            print(f"        fixed threshold      h = {values['crossing_fixed_threshold']:.3f}  "
                  f"(shift {values['shift_fixed']:+.3f})")
            print(f"        rescaled threshold   h = {values['crossing_rescaled_threshold']:.3f}  "
                  f"(shift {values['shift_rescaled']:+.3f})")
    print("\nwrote data/large_n_cut_analysis.json and figures/large_n_cut.png")


if __name__ == "__main__":
    main()
