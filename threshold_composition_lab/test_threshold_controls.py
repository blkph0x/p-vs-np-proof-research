"""Independent finite graph and exact affine-trade adversarial controls."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import unittest

from threshold_controls import (
    aggregation_control, build_or_gadget, make_trade_certificate, or_control,
    reference_signature, trade_control, verify_trade_certificate,
)


def input_digest(truth, features):
    """Recreate public input binding without calling the producer normalizer."""
    stream = bytearray(b"threshold-feature-trade-input-v2\0")

    def encode_unsigned(value):
        magnitude = value.to_bytes((value.bit_length() + 7) // 8, "big")
        stream.extend(len(magnitude).to_bytes(8, "big"))
        stream.extend(magnitude)

    encode_unsigned(len(truth))
    encode_unsigned(len(features[0]))
    for label, row in zip(truth, features):
        stream.append(int(label))
        for feature in row:
            value = Fraction(feature)
            stream.append(int(value.numerator < 0))
            encode_unsigned(abs(value.numerator))
            encode_unsigned(value.denominator)
    return sha256(stream).hexdigest()


def recursive_matching_cost(vertices, edges):
    """Second oracle: pair the first remaining vertex, never enumerate subsets."""
    if not vertices:
        return Fraction(0)
    vertex = min(vertices)
    candidates = []
    for u, v, cost in edges:
        if vertex == u and v in vertices:
            rest = recursive_matching_cost(vertices - {u, v}, edges)
        elif vertex == v and u in vertices:
            rest = recursive_matching_cost(vertices - {u, v}, edges)
        else:
            continue
        if rest is not None:
            candidates.append(rest + cost)
    return min(candidates) if candidates else None


class ThresholdControlsTests(unittest.TestCase):
    def test_or_all_physical_states_and_original_witnesses(self):
        total = checks = 0
        for k in range(1, 6):
            control = or_control(k)
            self.assertTrue(control["all_states_verified"])
            self.assertEqual(control["mismatches"], [])
            self.assertEqual(control["feasible_states"], 2 ** k)
            self.assertEqual(control["accepted_states"], 2 ** k - 1)
            self.assertEqual(control["invalid_physical_states"], 4 ** k - 2 ** k)
            for state in control["states"]:
                removed = {v for v in range(2 * k) if state["deleted_mask"] >> v & 1}
                independent = recursive_matching_cost(set(range(2 * k)) - removed,
                                                     control["edges"])
                self.assertEqual(state["minimum_cost"], independent)
                if state["feasible"]:
                    covered = []
                    cost = 0
                    for edge_id in state["witness_edge_ids"]:
                        u, v, weight = control["edges"][edge_id]
                        covered.extend((u, v))
                        cost += weight
                    self.assertEqual(len(covered), len(set(covered)))
                    self.assertEqual(set(covered), set(range(2 * k)) - removed)
                    self.assertEqual(cost, state["minimum_cost"])
                else:
                    self.assertIsNone(state["witness_edge_ids"])
                    self.assertFalse(state["accepted"])
            total += control["physical_states"]
            checks += control["edge_subset_checks"]
        self.assertEqual(total, 1364)
        self.assertEqual(checks, 37448)

    def test_reference_oracle_signed_rational_parallel_edges(self):
        edges = [(0, 1, Fraction(3, 2)), (2, 3, -2), (0, 2, -3),
                 (1, 3, 5), (0, 1, -1)]
        result = reference_signature(4, edges, [0, 1, 2, 3])
        for state in result["states"]:
            surviving = {v for v in range(4) if not state["deleted_mask"] >> v & 1}
            self.assertEqual(state["minimum_cost"], recursive_matching_cost(surviving, edges))
        self.assertEqual(result["states"][0]["minimum_cost"], -3)
        self.assertEqual(result["states"][0]["matching_count"], 3)
        self.assertEqual(reference_signature(0, [], [])["states"][0]["minimum_cost"], 0)
        mandatory = reference_signature(3, [(0, 1, 1), (1, 2, 2)], [0])
        self.assertIsNone(mandatory["states"][0]["minimum_cost"])
        self.assertEqual(mandatory["states"][1]["minimum_cost"], 2)

    def test_reference_budget_exact_boundary_and_input_validation(self):
        self.assertEqual(reference_signature(2, [(0, 1, 1)], [0, 1], max_checks=8)["edge_subset_checks"], 8)
        with self.assertRaises(ValueError):
            reference_signature(2, [(0, 1, 1)], [0, 1], max_checks=7)
        with self.assertRaises(ValueError):
            reference_signature(1000000000, [], [])
        bad_inputs = [(-1, [], []), (True, [], []), (2, [(0, 0, 1)], []),
                      (2, [(0, 2, 1)], []), (2, [(0, 1, 0.5)], []),
                      (2, [(0, 1, True)], []), (2, [], [0, 0]),
                      (2, [], [True]), (2, [], [2]), (2, [(0, 1)], [])]
        for n, edges, terminals in bad_inputs:
            with self.subTest(n=n, edges=edges, terminals=terminals):
                with self.assertRaises(ValueError):
                    reference_signature(n, edges, terminals)
        for k in (-1, 0, True, 1.5, 6):
            with self.assertRaises(ValueError):
                build_or_gadget(k)

    def test_aggregation_false_accept_and_no_satisfying_assignment(self):
        control = aggregation_control()
        self.assertFalse(control["formula_satisfiable"])
        self.assertEqual(control["false_accepts"], [[1, 1]])
        self.assertEqual(control["clause_cutoffs"], [0, 0, 1])
        self.assertEqual([row["total_cost"] for row in control["rows"]], [3, 2, 2, 1])
        last = control["rows"][-1]
        self.assertEqual(last["true_literal_counts"], [1, 0, 2])
        self.assertEqual(last["costs"], [0, 1, 0])
        self.assertTrue(last["sum_threshold_accepted"])
        self.assertFalse(last["formula_satisfied"])
        for row in control["rows"]:
            self.assertEqual(row["sum_threshold_accepted"], sum(row["true_literal_counts"]) >= 3)

    def test_original_four_point_trade_and_json_roundtrip(self):
        control = trade_control()
        certificate = json.loads(json.dumps(control["certificate"]))
        verdict = verify_trade_certificate(control["truth_table"], control["features"], certificate)
        self.assertTrue(verdict["valid"])
        self.assertEqual(verdict["mass_per_side"], 2)
        self.assertEqual(verdict["common_feature_sum"], [1, 1, 1, 1])
        self.assertEqual([control["assignments"][i] for i in certificate["accepted_indices"]],
                         [[1, 0, 1, 0], [0, 1, 0, 1]])
        self.assertEqual([control["assignments"][i] for i in certificate["rejected_indices"]],
                         [[1, 1, 0, 0], [0, 0, 1, 1]])
        # Every small signed affine coefficient choice obeys the certified sum
        # equality; this finite control supplements, rather than proves, the theorem.
        for weights in product(range(-2, 3), repeat=4):
            costs = [Fraction(-7, 3) + sum(w * x for w, x in zip(weights, row))
                     for row in control["features"]]
            left = sum(costs[i] for i in certificate["accepted_indices"])
            right = sum(costs[i] for i in certificate["rejected_indices"])
            self.assertEqual(left, right)
            for cutoff in sorted(set(costs)):
                self.assertNotEqual([cost <= cutoff for cost in costs], control["truth_table"])

    def test_truth_and_feature_changes_rejected_even_with_rebound_digest(self):
        original = trade_control()
        truth, features, certificate = original["truth_table"], original["features"], original["certificate"]
        changed_truth = truth.copy()
        changed_truth[10] = False
        self.assertFalse(verify_trade_certificate(changed_truth, features, certificate)["valid"])
        rebound = deepcopy(certificate)
        rebound["input_sha256"] = input_digest(changed_truth, features)
        verdict = verify_trade_certificate(changed_truth, features, rebound)
        self.assertFalse(verdict["valid"])
        self.assertIn("truth label", verdict["errors"][0])
        changed_features = deepcopy(features)
        changed_features[10][0] = 2
        self.assertFalse(verify_trade_certificate(truth, changed_features, certificate)["valid"])
        rebound["input_sha256"] = input_digest(truth, changed_features)
        verdict = verify_trade_certificate(truth, changed_features, rebound)
        self.assertFalse(verdict["valid"])
        self.assertIn("sums are unequal", verdict["errors"][0])
        # Binding covers the entire original input, including an unused row.
        unused_changed = truth.copy()
        unused_changed[0] = True
        self.assertFalse(verify_trade_certificate(unused_changed, features, certificate)["valid"])

    def test_nonlinear_features_really_change_the_classification_class(self):
        control = trade_control()
        positive = control["nonlinear_feature_positive_control"]
        self.assertTrue(positive["all_rows_correct"])
        self.assertEqual([-sum(row) <= -2 for row in positive["features"]], control["truth_table"])
        certificate = deepcopy(control["certificate"])
        certificate["input_sha256"] = input_digest(control["truth_table"], positive["features"])
        self.assertFalse(verify_trade_certificate(control["truth_table"], positive["features"], certificate)["valid"])

    def test_signed_rational_features_and_multisets(self):
        control = trade_control()
        features = [[Fraction(2 * bit - 5, j + 2) for j, bit in enumerate(row)]
                    for row in control["features"]]
        certificate = make_trade_certificate(control["truth_table"], features,
                                             [10, 5, 10, 5], [12, 3, 12, 3])
        verdict = verify_trade_certificate(control["truth_table"], features, certificate)
        self.assertTrue(verdict["valid"])
        self.assertEqual(verdict["mass_per_side"], 4)
        # Zero-dimensional features still admit a valid constant-score obstruction.
        empty = make_trade_certificate([True, False], [[], []], [0], [1])
        self.assertTrue(verify_trade_certificate([True, False], [[], []], empty)["valid"])

    def test_large_exact_features_do_not_require_decimal_conversion(self):
        # 2**15000 exceeds the default 4300 decimal-digit conversion limit.
        # Neither binding nor verification should stringify exact input numbers.
        large = 1 << 15000
        truth = [True, False]
        for value in (large, -large, Fraction(1, large), Fraction(-large, large + 1)):
            features = [[value], [value]]
            certificate = make_trade_certificate(truth, features, [0], [1])
            self.assertEqual(certificate["input_sha256"], input_digest(truth, features))
            self.assertTrue(verify_trade_certificate(truth, features, certificate)["valid"])
        # Signs, labels and dimensions have separate, unambiguous encodings.
        self.assertNotEqual(input_digest(truth, [[large], [large]]),
                            input_digest(truth, [[-large], [-large]]))
        self.assertNotEqual(input_digest(truth, [[1], [1]]),
                            input_digest(truth, [[1, 0], [1, 0]]))

    def test_malformed_and_forged_certificates_fail_closed(self):
        control = trade_control()
        truth, features, certificate = control["truth_table"], control["features"], control["certificate"]
        mutations = [None, {}, {**certificate, "extra": 1},
                     {**certificate, "kind": "trust_me"},
                     {**certificate, "input_sha256": "0" * 64},
                     {**certificate, "accepted_indices": []},
                     {**certificate, "accepted_indices": [10]},
                     {**certificate, "accepted_indices": [10, True]},
                     {**certificate, "accepted_indices": [10, 99]},
                     {**certificate, "accepted_indices": [10, 12]},
                     {**certificate, "accepted_indices": [10, 10]}]
        for mutated in mutations:
            self.assertFalse(verify_trade_certificate(truth, features, mutated)["valid"])
        invalid_data = [([1, False], [[0], [0]]), ([True], [[0.5]]),
                        ([True], [[True]]), ([True, False], [[0], []]),
                        ([], []), ([True], [])]
        for bad_truth, bad_features in invalid_data:
            self.assertFalse(verify_trade_certificate(bad_truth, bad_features, certificate)["valid"])
        with self.assertRaises(ValueError):
            make_trade_certificate(truth, features, [10, 10], [12, 3])

    def test_saved_results_replay_and_source_provenance(self):
        here = Path(__file__).resolve().parent
        saved_path = here / "RESULTS.json"
        if not saved_path.exists():
            self.skipTest("artifact has not yet been generated")
        saved = json.loads(saved_path.read_text(encoding="utf-8"))
        self.assertTrue(saved["source_unchanged_during_run"])
        for name, digest in saved["source_sha256"].items():
            self.assertEqual(sha256((here / name).read_bytes()).hexdigest(), digest)
        for control in saved["or_controls"]:
            self.assertEqual(or_control(control["k"]), control)
        self.assertEqual(aggregation_control(), saved["aggregation_counterexample"])
        trade = saved["affine_trade"]
        self.assertTrue(verify_trade_certificate(trade["truth_table"], trade["features"],
                                                trade["certificate"])["valid"])


if __name__ == "__main__":
    unittest.main()
