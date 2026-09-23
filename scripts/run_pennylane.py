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
    parser.add_argument("--qubits", type=int, default=6)
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--steps", type=int, default=120)
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


if __name__ == "__main__":
    main()
