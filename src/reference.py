"""Analytic reference boundaries for the ANNNI phase diagram.

Formulas as given in the QSITE 2026 Scientific Track handout (and its
`starter_kit/reference.py`):

    Ising (ferro <-> para, kappa < 0.5):  h = (1 - kappa)/kappa * (1 - sqrt((1 - 3k + 4k^2)/(1 - k)))
    BKT   (antiphase <-> floating):       h = 1.05 * (kappa - 0.5)
    KT    (floating <-> para):            h = 1.05 * sqrt((kappa - 0.5)(kappa - 0.1))

At finite system size these are qualitative reference lines, not exact
boundaries; the handout says so explicitly.

Note on kappa = 0: the closed form is singular there and the starter kit's
implementation returns 0.0, while the correct limit is h = 1.  We clamp kappa
away from 0 so the left edge of the grid is not mislabelled.
"""
from __future__ import annotations

import numpy as np

FERRO, PARA, ANTIPHASE, FLOATING = 0, 1, 2, 3
PHASE_NAMES = {FERRO: "ferromagnetic", PARA: "paramagnetic", ANTIPHASE: "antiphase", FLOATING: "floating"}
KAPPA_FLOOR = 1e-4


def ising_transition(kappa):
    kappa = np.maximum(np.asarray(kappa, dtype=float), KAPPA_FLOOR)
    inside = np.clip((1.0 - 3.0 * kappa + 4.0 * kappa ** 2) / np.maximum(1.0 - kappa, 1e-9), 0.0, None)
    values = (1.0 - kappa) * (1.0 - np.sqrt(inside)) / kappa
    return np.where(kappa < 0.5, values, np.nan)


def bkt_transition(kappa):
    kappa = np.asarray(kappa, dtype=float)
    return np.where(kappa > 0.5, 1.05 * (kappa - 0.5), np.nan)


def kt_transition(kappa):
    kappa = np.asarray(kappa, dtype=float)
    inside = np.clip((kappa - 0.5) * (kappa - 0.1), 0.0, None)
    return np.where(kappa > 0.5, 1.05 * np.sqrt(inside), np.nan)


def reference_labels(kappa_grid: np.ndarray, h_grid: np.ndarray) -> np.ndarray:
    """Label every grid cell using the analytic lines above."""
    labels = np.full(kappa_grid.shape, PARA, dtype=int)
    low = kappa_grid < 0.5
    high = ~low
    ising = ising_transition(kappa_grid)
    labels[low & (h_grid < ising)] = FERRO
    bkt, kt = bkt_transition(kappa_grid), kt_transition(kappa_grid)
    labels[high & (h_grid < bkt)] = ANTIPHASE
    labels[high & (h_grid >= bkt) & (h_grid < kt)] = FLOATING
    return labels
