"""PennyLane path: Hamiltonian, exact cross-check, and the noisy pipeline.

This is the code that produced the submitted noisy phase diagrams.  It needs
the Scientific Track environment (PennyLane 0.44.1):

    uv sync --project "Scientific Track"
    uv run --project "Scientific Track" python scripts/run_pennylane.py --check
    uv run --project "Scientific Track" python scripts/run_pennylane.py --scan --qubits 8 --grid 24

`--check` compares this Hamiltonian with the numpy reference in src/annni.py
element by element and passes.  `--scan` is the 58-minute run whose output is
committed as data/pennylane_scan_N8.npz; every figure and number that mentions
noise comes from it.
"""
from __future__ import annotations

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp


def build_hamiltonian(n_qubits: int, kappa: float, h: float, periodic: bool = True):
    """H = -sum Z_i Z_{i+1} + kappa sum Z_i Z_{i+2} - h sum X_i (starter-kit convention)."""
    coefficients, observables = [], []
    limit_nn = n_qubits if periodic else n_qubits - 1
    limit_nnn = n_qubits if periodic else n_qubits - 2
    for i in range(limit_nn):
        coefficients.append(-1.0)
        observables.append(qml.Z(i) @ qml.Z((i + 1) % n_qubits))
    for i in range(limit_nnn):
        coefficients.append(kappa)
        observables.append(qml.Z(i) @ qml.Z((i + 2) % n_qubits))
    for i in range(n_qubits):
        coefficients.append(-h)
        observables.append(qml.X(i))
    return qml.dot(coefficients, observables)


def exact_ground_state(n_qubits: int, kappa: float, h: float):
    matrix = qml.matrix(build_hamiltonian(n_qubits, kappa, h), wire_order=range(n_qubits))
    values, vectors = np.linalg.eigh(np.asarray(matrix))
    return np.asarray(vectors[:, 0]), float(values[0])


def correlators_from_state(state, n_qubits: int):
    """Exact <ZZ> at distance 1 and 2 for a state vector (used as the p=0 check)."""
    probabilities = np.abs(np.asarray(state)) ** 2
    probabilities = probabilities / probabilities.sum()
    index = np.arange(len(probabilities))
    bits = ((index[:, None] >> np.arange(n_qubits)[None, :]) & 1)
    z = 1 - 2 * bits
    nn = np.mean(z * np.roll(z, -1, axis=1), axis=1)
    nnn = np.mean(z * np.roll(z, -2, axis=1), axis=1)
    return float(probabilities @ nn), float(probabilities @ nnn)


def correlator_observables(n_qubits: int):
    nn = [qml.Z(i) @ qml.Z((i + 1) % n_qubits) for i in range(n_qubits)]
    nnn = [qml.Z(i) @ qml.Z((i + 2) % n_qubits) for i in range(n_qubits)]
    return nn, nnn


def ansatz(params, n_qubits: int, layers: int, noise: float = 0.0):
    """Hardware-efficient ring ansatz; depolarizing noise after each CNOT."""
    for i in range(n_qubits):
        qml.Hadamard(wires=i)
    for layer in range(layers):
        for i in range(n_qubits):
            qml.RY(params[layer, i, 0], wires=i)
            qml.RZ(params[layer, i, 1], wires=i)
        for i in range(n_qubits):
            target = (i + 1) % n_qubits
            qml.CNOT(wires=[i, target])
            if noise > 0.0:
                qml.DepolarizingChannel(noise, wires=target)


def vqe_ground_state(n_qubits: int, kappa: float, h: float, layers: int = 4,
                     steps: int = 150, seed: int = 0, stepsize: float = 0.05, init=None):
    """Optimise the ansatz on the noiseless device; returns the fitted parameters.

    `init` warm-starts from a neighbouring grid point, which both speeds up the
    fit and keeps it out of the poor local minima a cold start can fall into.
    """
    device = qml.device("default.qubit", wires=n_qubits)
    hamiltonian = build_hamiltonian(n_qubits, kappa, h)

    @qml.qnode(device)
    def cost(params):
        ansatz(params, n_qubits, layers)
        return qml.expval(hamiltonian)

    if init is None:
        rng = np.random.default_rng(seed)
        start = rng.normal(0.0, 0.1, size=(layers, n_qubits, 2))
    else:
        start = np.array(init, dtype=float)
    params = pnp.array(start, requires_grad=True)
    optimizer = qml.AdamOptimizer(stepsize=stepsize)
    for _ in range(steps):
        params = optimizer.step(cost, params)
    return params, float(cost(params))


def noisy_correlators(params, n_qubits: int, noise: float, layers: int = 4):
    """<ZZ> at distance 1 and 2 with depolarizing noise after every CNOT."""
    device = qml.device("default.mixed", wires=n_qubits)
    nn, nnn = correlator_observables(n_qubits)

    @qml.qnode(device)
    def circuit():
        ansatz(params, n_qubits, layers, noise=noise)
        return [qml.expval(o) for o in nn + nnn]

    values = np.asarray(circuit(), dtype=float)
    return float(values[:n_qubits].mean()), float(values[n_qubits:].mean())


def cross_check(n_qubits: int = 6, points=((0.2, 0.4), (0.8, 0.2), (0.5, 1.5))):
    """Compare the PennyLane Hamiltonian with the numpy reference path."""
    from .annni import AnnniChain

    chain = AnnniChain(n_qubits)
    report = []
    for kappa, h in points:
        matrix = np.asarray(qml.matrix(build_hamiltonian(n_qubits, kappa, h), wire_order=range(n_qubits)))
        difference = float(np.max(np.abs(matrix - chain.hamiltonian(kappa, h))))
        state, energy = chain.ground_state(kappa, h)
        _, energy_pl = exact_ground_state(n_qubits, kappa, h)
        report.append({"kappa": kappa, "h": h, "max_matrix_difference": difference,
                       "energy_numpy": energy, "energy_pennylane": energy_pl})
    return report
