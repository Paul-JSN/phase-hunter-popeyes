"""PLACEHOLDER noise model - not the model the challenge requires.

The challenge's noise model is a depolarizing channel on the target qubit after
every CNOT of the state-preparation circuit, simulated on PennyLane's
`default.mixed` device.  That pipeline lives in `src/pennylane_pipeline.py` and
has to run in the track environment, which needs PennyLane installed.

Until those runs exist, this module provides a deliberately crude stand-in so
the game and the plots have something to show: a single global depolarizing
channel applied to the exact ground state,

    rho = (1 - q) |psi><psi| + q * I / 2^N,

which leaves every Z-correlator scaled by (1 - q).  We set q from an effective
gate count, q = 1 - (1 - p)^(gates).  This reproduces the qualitative effect
(ordered phases fade toward the paramagnet) but NOT the correct per-phase
structure, so nothing produced here may be reported as a noise result.
"""
from __future__ import annotations

import numpy as np

PLACEHOLDER = True


def effective_q(p: float, gates: int) -> float:
    return 1.0 - (1.0 - p) ** gates


def apply(zz1: np.ndarray, zz2: np.ndarray, p: float, gates: int = 24):
    q = effective_q(p, gates)
    return (1.0 - q) * zz1, (1.0 - q) * zz2, q
