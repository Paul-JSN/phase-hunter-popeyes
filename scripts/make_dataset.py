"""Scan the (kappa, h) plane with exact ground states and classify the phases.

    python3 scripts/make_dataset.py --qubits 8 --grid 40                    # numpy
    python3 scripts/make_dataset.py --qubits 8 --grid 40 --backend pennylane

Both backends diagonalise the same Hamiltonian; --backend pennylane builds it
with qml.dot and takes the ground state from qml.matrix, so the submitted clean
diagram is a PennyLane product and the numpy path in src/annni.py is the
cross-check rather than the source. run_pennylane.py --check already compares
the two matrices element by element; this compares the observables they give.

Writes data/grid_N{n}.npz and data/summary.json, which scripts/make_figures.py
turns into the clean-diagram figures. The game's own dataset is built by
scripts/make_stages.py - this script does not touch it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.annni import AnnniChain
from src.classify import accuracy, classify
from src.reference import FLOATING, reference_labels


def pennylane_grid(n_qubits, kappas, hs, chain):
    """The same scan through PennyLane, with the numpy path kept as a cross-check.

    Per-shot standard deviations still come from src/annni.py: they are a property
    of the state, not of the library that produced it, and the two states are
    compared point by point here.
    """
    from src.pennylane_pipeline import correlators_from_state, exact_ground_state

    shape = (len(hs), len(kappas))
    out = {k: np.zeros(shape) for k in ("zz1", "zz2", "sd1", "sd2")}
    worst_state, worst_energy = 0.0, 0.0
    for b, kappa in enumerate(kappas):
        for a, h in enumerate(hs):
            state, energy = exact_ground_state(n_qubits, float(kappa), float(h))
            zz1, zz2 = correlators_from_state(state, n_qubits)
            reference_state, reference_energy = chain.ground_state(float(kappa), float(h))
            reference = chain.measure(reference_state)
            out["zz1"][a, b], out["zz2"][a, b] = zz1, zz2
            out["sd1"][a, b], out["sd2"][a, b] = reference["sd1"], reference["sd2"]
            worst_state = max(worst_state, abs(zz1 - reference["zz1"]), abs(zz2 - reference["zz2"]))
            worst_energy = max(worst_energy, abs(energy - reference_energy))
        print(f"  kappa {kappa:.3f}  ({b + 1}/{len(kappas)})", end="\r", flush=True)
    print(f"\ncross-check against the numpy path: correlators agree to {worst_state:.2e}, "
          f"energies to {worst_energy:.2e}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=8)
    parser.add_argument("--grid", type=int, default=40)
    parser.add_argument("--backend", choices=("numpy", "pennylane"), default="numpy")
    arguments = parser.parse_args()

    kappas = np.linspace(0.0, 1.0, arguments.grid)
    hs = np.linspace(0.0, 2.0, arguments.grid)
    chain = AnnniChain(arguments.qubits)

    start = time.time()
    if arguments.backend == "numpy":
        grid = chain.grid(kappas, hs)
    else:
        grid = pennylane_grid(arguments.qubits, kappas, hs, chain)
    elapsed = time.time() - start

    kappa_grid, h_grid = np.meshgrid(kappas, hs)
    reference = reference_labels(kappa_grid, h_grid)
    predicted = classify(grid["zz1"], grid["zz2"], kappas, hs)
    scores = accuracy(predicted, reference)

    (ROOT / "data").mkdir(exist_ok=True)
    np.savez_compressed(ROOT / f"data/grid_N{arguments.qubits}.npz", kappas=kappas, hs=hs,
                        reference=reference, predicted=predicted, **grid)

    summary = {
        "backend": arguments.backend,
        "qubits": arguments.qubits,
        "grid": [arguments.grid, arguments.grid],
        "ground_states": int(arguments.grid ** 2),
        "seconds": round(elapsed, 2),
        **{k: round(v, 4) for k, v in scores.items()},
    }
    (ROOT / "data/summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
