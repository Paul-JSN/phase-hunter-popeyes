"""Run the PennyLane path: cross-check, then the noisy correlator pipeline.

    uv run --project "Scientific Track" python scripts/run_pennylane.py --check
    uv run --project "Scientific Track" python scripts/run_pennylane.py --noise-pilot

`--check` verifies that the PennyLane Hamiltonian matches the numpy reference
path used for the current figures.  `--noise-pilot` fits the ansatz at a few
(kappa, h) points and measures the correlators at p = 0, 0.01, 0.05 with
depolarizing noise after every CNOT, reporting the wall-clock time per point so
the grid size for the full noisy scan can be chosen from data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--noise-pilot", action="store_true")
    parser.add_argument("--scan", action="store_true", help="full (kappa, h) scan at every noise level")
    parser.add_argument("--qubits", type=int, default=6)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--warm-steps", type=int, default=60, help="steps for a warm-started fit")
    parser.add_argument("--grid", type=int, default=30)
    parser.add_argument("--noise", type=float, nargs="*", default=[0.0, 0.01, 0.05])
    parser.add_argument("--energy-tol", type=float, default=0.05,
                        help="refit from a cold start when the VQE energy is this far above exact")
    arguments = parser.parse_args()

    from src.pennylane_pipeline import cross_check, noisy_correlators, vqe_ground_state

    if arguments.check:
        for row in cross_check(arguments.qubits):
            print(json.dumps(row))

    if arguments.noise_pilot:
        points = [(0.2, 0.4), (0.8, 0.2), (0.5, 1.5)]
        results = []
        for kappa, h in points:
            start = time.time()
            params, energy = vqe_ground_state(arguments.qubits, kappa, h,
                                              layers=arguments.layers, steps=arguments.steps)
            fit_seconds = time.time() - start
            row = {"kappa": kappa, "h": h, "vqe_energy": energy, "fit_seconds": round(fit_seconds, 2)}
            for p in (0.0, 0.01, 0.05):
                start = time.time()
                zz1, zz2 = noisy_correlators(params, arguments.qubits, p, layers=arguments.layers)
                row[f"p{p}"] = {"zz1": round(zz1, 4), "zz2": round(zz2, 4),
                                "seconds": round(time.time() - start, 2)}
            results.append(row)
            print(json.dumps(row))
        (ROOT / "data").mkdir(exist_ok=True)
        (ROOT / "data/noise_pilot.json").write_text(json.dumps(results, indent=2))

    if arguments.scan:
        scan(arguments)


def scan(arguments) -> None:
    """Sweep the plane: VQE at every point, then correlators at each noise level.

    Each column of constant kappa is swept upward in h with the previous fit as
    the starting point. Every fit is compared against exact diagonalisation and
    refitted from a cold start if it landed too high, so a bad local minimum
    cannot quietly become a phase boundary.
    """
    import numpy as np

    from src.annni import AnnniChain
    from src.pennylane_pipeline import (correlators_from_state, noisy_correlators, vqe_ground_state)

    n = arguments.qubits
    chain = AnnniChain(n)
    kappas = np.linspace(0.0, 1.0, arguments.grid)
    hs = np.linspace(0.0, 2.0, arguments.grid)
    shape = (len(hs), len(kappas))
    out = {f"p{p}_{key}": np.zeros(shape) for p in arguments.noise for key in ("zz1", "zz2")}
    out.update({k: np.zeros(shape) for k in ("exact_zz1", "exact_zz2", "energy_vqe", "energy_exact", "refits")})

    started = time.time()
    for b, kappa in enumerate(kappas):
        params = None
        for a, h in enumerate(hs):
            state, energy_exact = chain.ground_state(float(kappa), float(h))
            steps = arguments.warm_steps if params is not None else arguments.steps
            params, energy = vqe_ground_state(n, float(kappa), float(h), layers=arguments.layers,
                                              steps=steps, init=params)
            if energy - energy_exact > arguments.energy_tol:      # bad minimum: start over
                params, energy = vqe_ground_state(n, float(kappa), float(h), layers=arguments.layers,
                                                  steps=arguments.steps, init=None)
                out["refits"][a, b] = 1
            out["energy_vqe"][a, b], out["energy_exact"][a, b] = energy, energy_exact
            out["exact_zz1"][a, b], out["exact_zz2"][a, b] = correlators_from_state(state, n)
            for p in arguments.noise:
                zz1, zz2 = noisy_correlators(params, n, p, layers=arguments.layers)
                out[f"p{p}_zz1"][a, b], out[f"p{p}_zz2"][a, b] = zz1, zz2
        done = (b + 1) / len(kappas)
        elapsed = time.time() - started
        print(f"kappa {kappa:.3f}  {done:6.1%}  elapsed {elapsed/60:5.1f} min  "
              f"eta {elapsed/done*(1-done)/60:5.1f} min  refits {int(out['refits'].sum())}", flush=True)
        np.savez_compressed(ROOT / f"data/pennylane_scan_N{n}.npz", kappas=kappas, hs=hs,
                            noise=np.array(arguments.noise), columns_done=b + 1, **out)

    error = np.abs(out["energy_vqe"] - out["energy_exact"])
    print(json.dumps({"qubits": n, "grid": arguments.grid, "minutes": round((time.time() - started) / 60, 1),
                      "vqe_energy_error_mean": float(error.mean()), "vqe_energy_error_max": float(error.max()),
                      "refits": int(out["refits"].sum())}, indent=2))


if __name__ == "__main__":
    main()
