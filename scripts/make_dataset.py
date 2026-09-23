"""Scan the (kappa, h) plane with exact ground states and classify the phases.

    python3 scripts/make_dataset.py --qubits 8 --grid 40

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=8)
    parser.add_argument("--grid", type=int, default=40)
    arguments = parser.parse_args()

    kappas = np.linspace(0.0, 1.0, arguments.grid)
    hs = np.linspace(0.0, 2.0, arguments.grid)
    chain = AnnniChain(arguments.qubits)

    start = time.time()
    grid = chain.grid(kappas, hs)
    elapsed = time.time() - start

    kappa_grid, h_grid = np.meshgrid(kappas, hs)
    reference = reference_labels(kappa_grid, h_grid)
    predicted = classify(grid["zz1"], grid["zz2"], kappas, hs)
    scores = accuracy(predicted, reference)

    (ROOT / "data").mkdir(exist_ok=True)
    np.savez_compressed(ROOT / f"data/grid_N{arguments.qubits}.npz", kappas=kappas, hs=hs,
                        reference=reference, predicted=predicted, **grid)

    summary = {
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
