"""Unsupervised phase classification from measured correlators.

Features per (kappa, h) cell: the nearest-neighbour correlator <Z_i Z_{i+1}>
and the next-nearest one <Z_i Z_{i+2}>.  We run Lloyd's algorithm (k-means)
with three centroids seeded at three corners of the parameter plane whose
phase is not in doubt, so each cluster keeps a fixed physical identity:

    ferromagnetic  low kappa,  low h      both correlators positive
    antiphase      high kappa, low h      <ZZ_1> ~ 0, <ZZ_2> negative
    paramagnetic   high h                 both correlators small

The floating phase is not one of the clusters: it is a narrow sliver that the
handout warns is very hard to resolve at small system size.  We report
accuracy both with those cells excluded and with them counted as errors.
"""
from __future__ import annotations

import numpy as np

from .reference import ANTIPHASE, FERRO, FLOATING, PARA

ANCHORS = {FERRO: (0.05, 0.05), ANTIPHASE: (0.95, 0.05), PARA: (0.50, 1.95)}


def _features(zz1: np.ndarray, zz2: np.ndarray) -> np.ndarray:
    return np.stack([zz1.ravel(), zz2.ravel()], axis=1)


def fit_centroids(zz1: np.ndarray, zz2: np.ndarray, kappas: np.ndarray, hs: np.ndarray,
                  iterations: int = 50) -> np.ndarray:
    """Cluster centres in (correlator) space, in the fixed order ferro, antiphase, para."""
    points = _features(zz1, zz2)
    order = [FERRO, ANTIPHASE, PARA]
    centroids = []
    for label in order:
        kappa, h = ANCHORS[label]
        a = int(np.argmin(np.abs(hs - h)))
        b = int(np.argmin(np.abs(kappas - kappa)))
        centroids.append([zz1[a, b], zz2[a, b]])
    centroids = np.array(centroids, dtype=float)

    for _ in range(iterations):
        distances = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
        assignment = np.argmin(distances, axis=1)
        moved = np.array([points[assignment == k].mean(axis=0) if np.any(assignment == k)
                          else centroids[k] for k in range(len(order))])
        if np.allclose(moved, centroids):
            centroids = moved
            break
        centroids = moved

    return centroids


ORDER = [FERRO, ANTIPHASE, PARA]


def assign(zz1: np.ndarray, zz2: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """Label every cell by its nearest centroid, without re-fitting.

    Passing centroids fitted on the noiseless data is what a practitioner does
    when they calibrate a classifier on clean simulations and then apply it to
    noisy hardware, so it is the version that shows boundaries moving.
    """
    points = _features(zz1, zz2)
    distances = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
    return np.array(ORDER)[np.argmin(distances, axis=1)].reshape(zz1.shape)


def classify(zz1: np.ndarray, zz2: np.ndarray, kappas: np.ndarray, hs: np.ndarray,
             iterations: int = 50) -> np.ndarray:
    """Cluster and label in one step, re-fitting the centres on this data."""
    return assign(zz1, zz2, fit_centroids(zz1, zz2, kappas, hs, iterations))


def accuracy(predicted: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    """Cell accuracy against the analytic reference labels."""
    detectable = reference != FLOATING
    return {
        "accuracy_excluding_floating": float((predicted[detectable] == reference[detectable]).mean()),
        "accuracy_all_cells": float((predicted == reference).mean()),
        "floating_cell_fraction": float((~detectable).mean()),
    }
