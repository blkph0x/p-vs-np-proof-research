"""Tests for the exact full-transform cost audit."""
import json
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent / "fourier_spectrum_boundary_lab"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cost = load("fwht_cost")
reviewer = load("review_fwht_cost")


class FWHTCostAuditTests(unittest.TestCase):
    def test_exact_cost_formula_and_direct_counts(self):
        for dimension in range(0, 9):
            values = list(range(1 << dimension))
            _, fwht_counts = cost.counted_fwht(values)
            _, zeta_counts = cost.counted_subset_zeta(values)
            expected = dimension * (1 << dimension) // 2
            self.assertEqual(fwht_counts["butterflies"], expected)
            self.assertEqual(fwht_counts["arithmetic_operations"], 2 * expected)
            self.assertEqual(zeta_counts["additions"], expected)

    def test_saved_artifact_and_independent_replay(self):
        artifact = json.loads((ROOT / "FWHT_COST_RESULTS.json").read_text())
        self.assertEqual(len(artifact["rows"]), 21)
        self.assertEqual(artifact["rows"][-1]["state_count"], 1 << 20)
        self.assertEqual(artifact["rows"][-1]["fwht_arithmetic_operations"], 20 * (1 << 20))
        result = reviewer.review()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
