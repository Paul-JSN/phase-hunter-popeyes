"""Exact ground states of the 1D ANNNI chain (numpy reference path).

Convention follows the QSITE 2026 Scientific Track starter kit:

    H = - sum_i Z_i Z_{i+1} + kappa * sum_i Z_i Z_{i+2} - h * sum_i X_i

with periodic boundary conditions. The starter kit's own `exact_diag.py`
builds the same dense matrix with numpy and diagonalises it with
`numpy.linalg.eigh`; this module does the same thing with bit-arithmetic so a
40x40 grid at N=8 runs in seconds. `src/pennylane_pipeline.py` builds the same
Hamiltonian with PennyLane and is used to cross-check this path.
"""
from __future__ import annotations

import numpy as np


class AnnniChain:
    """Dense ANNNI solver for a ring of `n_qubits` spins."""

    def __init__(self, n_qubits: int = 8) -> None:
        self.n = n_qubits
        self.dim = 2 ** n_qubits
        idx = np.arange(self.dim)
        bits = ((idx[:, None] >> np.arange(n_qubits)[None, :]) & 1)
        self.z = 1 - 2 * bits                      # (dim, n) eigenvalues of Z_i
        # per-basis-state averages of the two correlators we use as observables
        self.zz1 = np.mean(self.z * np.roll(self.z, -1, axis=1), axis=1)
        self.zz2 = np.mean(self.z * np.roll(self.z, -2, axis=1), axis=1)
        # sum_i X_i as a (dim, dim) permutation-sum matrix
        self.xsum = np.zeros((self.dim, self.dim))
        for i in range(n_qubits):
            self.xsum[idx, idx ^ (1 << i)] += 1.0

    def hamiltonian(self, kappa: float, h: float) -> np.ndarray:
        diag = -self.n * self.zz1 + kappa * self.n * self.zz2
        return np.diag(diag) - h * self.xsum

    def ground_state(self, kappa: float, h: float) -> tuple[np.ndarray, float]:
        if self.n >= 10:                      # dense eigh gets expensive; Lanczos does not
            return self._ground_state_sparse(kappa, h)
        values, vectors = np.linalg.eigh(self.hamiltonian(kappa, h))
        return vectors[:, 0], float(values[0])

    def _ground_state_sparse(self, kappa: float, h: float) -> tuple[np.ndarray, float]:
        import scipy.sparse as sp
        import scipy.sparse.linalg as sla

        index = np.arange(self.dim)
        diagonal = (-np.sum(self.z * np.roll(self.z, -1, axis=1), axis=1)
                    + kappa * np.sum(self.z * np.roll(self.z, -2, axis=1), axis=1))
        matrix = sp.diags(diagonal).tocsr()
        if h:
            for site in range(self.n):
                flipped = index ^ (1 << site)
                matrix = matrix + sp.csr_matrix((-h * np.ones(self.dim), (index, flipped)),
                                                shape=(self.dim, self.dim))
        values, vectors = sla.eigsh(matrix, k=1, which="SA", maxiter=8000)
        return np.asarray(vectors[:, 0]), float(values[0])

    def measure(self, state: np.ndarray) -> dict[str, float]:
        """Exact expectation values and per-shot standard deviations.

        The standard deviations describe one Z-basis measurement of the whole
        register, which is what a shot costs in the game.
        """
        probs = np.abs(state) ** 2
        probs = probs / probs.sum()
        c1 = float(probs @ self.zz1)
        c2 = float(probs @ self.zz2)
        v1 = float(probs @ (self.zz1 ** 2)) - c1 ** 2
        v2 = float(probs @ (self.zz2 ** 2)) - c2 ** 2
        return {
            "zz1": c1,
            "zz2": c2,
            "sd1": float(np.sqrt(max(v1, 0.0))),
            "sd2": float(np.sqrt(max(v2, 0.0))),
        }

    def sample(self, state: np.ndarray, shots: int, rng: np.random.Generator) -> dict[str, float]:
        """Sample `shots` Z-basis measurements and average the correlators."""
        probs = np.abs(state) ** 2
        probs = probs / probs.sum()
        draws = rng.choice(self.dim, size=shots, p=probs)
        return {"zz1": float(self.zz1[draws].mean()), "zz2": float(self.zz2[draws].mean())}

    def grid(self, kappas: np.ndarray, hs: np.ndarray) -> dict[str, np.ndarray]:
        """Scan the (kappa, h) plane. Arrays are indexed [h_index, kappa_index]."""
        shape = (len(hs), len(kappas))
        out = {k: np.zeros(shape) for k in ("zz1", "zz2", "sd1", "sd2", "energy")}
        for a, h in enumerate(hs):
            for b, kappa in enumerate(kappas):
                state, energy = self.ground_state(float(kappa), float(h))
                summary = self.measure(state)
                for key in ("zz1", "zz2", "sd1", "sd2"):
                    out[key][a, b] = summary[key]
                out["energy"][a, b] = energy
        return out
