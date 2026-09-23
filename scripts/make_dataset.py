"""Scan the (kappa, h) plane, classify the phases, and export the game dataset.

    python3 scripts/make_dataset.py --qubits 8 --grid 40

Writes data/grid_N{n}.npz, data/game_dataset.json and the clean-diagram figures.
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
from src.noise_preview import apply as apply_noise_preview
from src.reference import FLOATING, reference_labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=8)
    parser.add_argument("--grid", type=int, default=40)
    parser.add_argument("--preview-noise", type=float, nargs="*", default=[0.01, 0.05])
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

    levels = [{"name": "clean", "p": 0.0, "zz1": grid["zz1"], "zz2": grid["zz2"], "placeholder": False}]
    for p in arguments.preview_noise:
        zz1, zz2, q = apply_noise_preview(grid["zz1"], grid["zz2"], p)
        levels.append({"name": f"preview_p{p}", "p": p, "zz1": zz1, "zz2": zz2,
                       "placeholder": True, "effective_q": q})

    dataset = {
        "note": ("Level 'clean' is exact diagonalisation at p = 0. Levels named preview_* use the "
                 "PLACEHOLDER global depolarizing model in src/noise_preview.py, not the challenge's "
                 "per-CNOT model, and must not be reported as noise results."),
        "qubits": arguments.qubits,
        "kappas": kappas.tolist(),
        "hs": hs.tolist(),
        "reference": reference.tolist(),
        "sd1": np.round(grid["sd1"], 4).tolist(),
        "sd2": np.round(grid["sd2"], 4).tolist(),
        "levels": [{"name": level["name"], "p": level["p"], "placeholder": level["placeholder"],
                    "zz1": np.round(level["zz1"], 4).tolist(),
                    "zz2": np.round(level["zz2"], 4).tolist()} for level in levels],
    }
    (ROOT / "game").mkdir(exist_ok=True)
    payload = json.dumps(dataset)
    (ROOT / "game/dataset.json").write_text(payload)
    # dataset.js lets index.html open straight from disk (file:// blocks fetch)
    (ROOT / "game/dataset.js").write_text("window.PHASE_HUNTER_DATA = " + payload + ";\n")

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
