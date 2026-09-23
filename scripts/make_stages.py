"""Build the five game stages and write game/dataset.js.

    python3 scripts/make_stages.py

Each stage is a different physical situation, not a reskin: different ring
length, or different gate noise. Ground truth for a stage is the phase
classification of that stage's own data, so a player is scored against what is
really there at that size rather than against the thermodynamic-limit lines.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.annni import AnnniChain
from src.classify import classify
from src.reference import reference_labels

GRID = 24
STAGES = [
    {"id": "clean8",  "name": "Clear skies", "sub": "8 spins · no interference",
     "qubits": 8, "p": 0.0, "source": "exact"},
    {"id": "noise01", "name": "Static", "sub": "8 spins · 1% gate errors",
     "qubits": 8, "p": 0.01, "source": "scan"},
    {"id": "noise05", "name": "Whiteout", "sub": "8 spins · 5% gate errors",
     "qubits": 8, "p": 0.05, "source": "scan"},
    {"id": "short6",  "name": "Broken ring", "sub": "6 spins · the stripes cannot fit",
     "qubits": 6, "p": 0.0, "source": "exact"},
    {"id": "long12",  "name": "Long chain", "sub": "12 spins · sharper borders",
     "qubits": 12, "p": 0.0, "source": "exact"},
]


def main() -> None:
    kappas = np.linspace(0.0, 1.0, GRID)
    hs = np.linspace(0.0, 2.0, GRID)
    reference = reference_labels(*np.meshgrid(kappas, hs))
    scan = np.load(ROOT / "data/pennylane_scan_N8.npz")
    payload = {"grid": GRID, "kappas": kappas.round(4).tolist(), "hs": hs.round(4).tolist(),
               "reference": reference.tolist(), "stages": [],
               "note": ("Stages differ by ring length and gate noise. Noisy stages come from the "
                        "PennyLane scan (VQE prep, depolarizing channel after every CNOT, "
                        "default.mixed); clean stages are exact ground states. Ground truth per "
                        "stage is that stage's own phase classification.")}

    for stage in STAGES:
        started = time.time()
        chain = AnnniChain(stage["qubits"])
        grid = chain.grid(kappas, hs)                      # exact: correlators + shot-noise widths
        if stage["source"] == "scan":
            zz1, zz2 = scan[f"p{stage['p']}_zz1"], scan[f"p{stage['p']}_zz2"]
        else:
            zz1, zz2 = grid["zz1"], grid["zz2"]
        truth = classify(zz1, zz2, kappas, hs)
        agreement = float((truth[reference != 3] == reference[reference != 3]).mean())
        payload["stages"].append({
            "id": stage["id"], "name": stage["name"], "sub": stage["sub"],
            "qubits": stage["qubits"], "p": stage["p"], "source": stage["source"],
            "zz1": np.round(zz1, 3).tolist(), "zz2": np.round(zz2, 3).tolist(),
            "sd1": np.round(grid["sd1"], 3).tolist(), "sd2": np.round(grid["sd2"], 3).tolist(),
            "truth": truth.tolist(), "agreement_with_analytic": round(agreement, 4)})
        print(f"{stage['id']:8} N={stage['qubits']:2} p={stage['p']:<5} "
              f"agreement with analytic lines {agreement:6.1%}   [{time.time()-started:.1f}s]")

    text = json.dumps(payload)
    (ROOT / "game/dataset.json").write_text(text)
    (ROOT / "game/dataset.js").write_text("window.PHASE_HUNTER_DATA = " + text + ";\n")
    print(f"\nwrote game/dataset.js  ({len(text)/1024:.0f} KB, {len(payload['stages'])} stages)")


if __name__ == "__main__":
    main()
