"""Checks for the comparison's scientific sampling and generated data contract."""
import json
from pathlib import Path
import unittest

import numpy as np

from scripts.make_comparison import (
    build_report, classify_features, draw_joint_means, exponential_extrapolation,
    finite_shot_experiment, linear_extrapolation, load_validated_archives,
)
from src.classify import assign, fit_centroids

ROOT = Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan, cls.readout, cls.validation = load_validated_archives()

    def test_recovered_probabilities_reproduce_the_source_circuit(self):
        self.assertLess(self.validation["readout_mean_max_difference"], 1e-7)
        self.assertEqual(self.readout["readout"].shape[:3], (3, 24, 24))

    def test_joint_sampling_and_linear_variance_match_readout_distribution(self):
        # The two observables come from the same register shot, so validate the
        # complete covariance matrix, including the off-diagonal entry.
        probabilities = self.readout["readout"][[1, 2], 8, 5]
        outcomes = self.readout["outcomes"]
        means = probabilities @ outcomes
        covariances = []
        for probability, mean in zip(probabilities, means):
            centered = outcomes - mean
            covariances.append((centered.T * probability) @ centered)
        half_budget, repeats = 50, 30000
        rng = np.random.default_rng(72)
        draws = [draw_joint_means(rng, np.broadcast_to(p, (repeats, len(p))),
                                  outcomes, half_budget) for p in probabilities]
        np.testing.assert_allclose(draws[0].mean(0), means[0], atol=.002)
        np.testing.assert_allclose(np.cov(draws[0].T), covariances[0] / half_budget,
                                   atol=.00015)
        corrected = linear_extrapolation(*draws)
        np.testing.assert_allclose(corrected.mean(0), linear_extrapolation(*means), atol=.002)
        expected_covariance = (1.25 ** 2 * covariances[0] + .25 ** 2 * covariances[1]) / half_budget
        np.testing.assert_allclose(np.cov(corrected.T), expected_covariance, atol=.0002)
        # Clipping extrapolates changes the estimator and its bias/variance.
        self.assertAlmostEqual(float(linear_extrapolation(np.array(1.), np.array(-1.))), 1.5)

    def test_class_code_order_and_fixed_rule_match_existing_classifier(self):
        scan = self.scan
        centroids = fit_centroids(scan["p0.0_zz1"], scan["p0.0_zz2"], scan["kappas"], scan["hs"])
        features = np.stack([scan["p0.05_zz1"], scan["p0.05_zz2"]], -1)
        np.testing.assert_array_equal(classify_features(features, centroids),
                                      assign(features[..., 0], features[..., 1], centroids))
        np.testing.assert_array_equal(classify_features(centroids, centroids), [0, 2, 1])

    def test_map_correction_matches_archived_second_method(self):
        expected = json.loads((ROOT / "data/second_method.json").read_text())["zero_noise_extrapolation"]
        maes = []
        for key in ("zz1", "zz2"):
            corrected = exponential_extrapolation(self.scan[f"p0.01_{key}"], self.scan[f"p0.05_{key}"])
            mae = float(np.abs(corrected - self.scan[f"p0.0_{key}"]).mean())
            self.assertAlmostEqual(mae, expected["mean_abs_error_after"][key]["exponential"], places=12)
            maes.append(mae)
        exported = json.loads((ROOT / "data/comparison.json").read_text())
        self.assertAlmostEqual(exported["maps"]["corrected"]["signal_mae"], np.mean(maes), places=12)

    def test_reproducible_protocol_and_exported_contract(self):
        first = build_report(repeats=4, budgets=(20,), seed=54)
        second = build_report(repeats=4, budgets=(20,), seed=54)
        self.assertEqual(first, second)
        self.assertEqual(first["finite_shots"]["results"][0]["total_shots_per_map"], 20 * 576)
        with self.assertRaises(ValueError):
            finite_shot_experiment(None, None, None, None, None, budgets=(21,))
        exported = json.loads((ROOT / "data/comparison.json").read_text())
        browser_text = (ROOT / "game/comparison-data.js").read_text()
        browser = json.loads(browser_text.split("window.PHASE_COMPARISON = ", 1)[1].rstrip(";\n"))
        self.assertEqual(browser, exported)
        self.assertEqual(exported["finite_shots"]["seeds"], 200)
        for name, row in exported["maps"].items():
            labels = np.asarray(row["labels"])
            self.assertEqual(labels.shape, (24, 24))
            self.assertTrue(set(labels.ravel()) <= {0, 1, 2})
            self.assertAlmostEqual(sum(row["phase_areas"].values()), 1)
            self.assertEqual(row["agreement_to_clean"], float(np.mean(
                labels == np.asarray(exported["maps"]["clean"]["labels"]))))


if __name__ == "__main__":
    unittest.main()
