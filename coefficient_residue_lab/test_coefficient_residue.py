"""Independent bounded expansion and adversarial coefficient-certificate tests."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
from math import lcm
from pathlib import Path
import random
import unittest

from coefficient_residue import (
    build_coefficient_proof, joint_residue_proof, verify_choice_witness,
    verify_coefficient_proof,
)


def independent_expansion(choices, *, max_factors=10):
    if len(choices) > max_factors:
        raise ValueError("independent enumeration factor cap exceeded")
    counts = Counter()
    words = {}
    for bits in product((0, 1), repeat=len(choices)):
        weight = sum(choices[i][bit] for i, bit in enumerate(bits))
        counts[weight] += 1
        words.setdefault(weight, list(bits))
    return counts, words


def certificate_binding(choices, target, modulus):
    """Independent serialization of the documented external-input binding."""
    data = bytearray(b"binary-product-coefficients-v1\0")

    def number(value):
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        data.extend(len(raw).to_bytes(8, "big"))
        data.extend(raw)

    number(len(choices))
    for pair in choices:
        for value in pair:
            number(value)
    number(target)
    data.append(int(modulus is not None))
    if modulus is not None:
        number(modulus)
    return sha256(data).hexdigest()


class CoefficientResidueTests(unittest.TestCase):
    def check_product(self, choices, target, moduli):
        expansion, _ = independent_expansion(choices)
        full = build_coefficient_proof(choices, target)
        self.assertEqual(full["status"], "EXACT")
        self.assertEqual(dict(full["certificate"]["layers"][-1]), dict(expansion))
        self.assertEqual(full["target_coefficient"], expansion[target])
        self.assertTrue(verify_coefficient_proof(choices, target, full["certificate"])["valid"])
        for modulus in moduli:
            folded = Counter()
            for exponent, count in expansion.items():
                folded[exponent % modulus] += count
            cyclic = build_coefficient_proof(choices, target, modulus=modulus)
            self.assertEqual(cyclic["status"], "EXACT")
            self.assertEqual(dict(cyclic["certificate"]["layers"][-1]), dict(folded))
            self.assertEqual(cyclic["target_coefficient"], folded[target % modulus])
            self.assertTrue(verify_coefficient_proof(choices, target, cyclic["certificate"], modulus=modulus)["valid"])
            if cyclic["attainable"]:
                self.assertTrue(verify_choice_witness(choices, target, cyclic["witness"], modulus=modulus)["valid"])

    def test_all_tiny_products_and_exact_folding(self):
        pairs = list(product(range(3), repeat=2))
        cases = 0
        for size in range(4):
            for choices in product(pairs, repeat=size):
                self.check_product(choices, size + 1, (1, 2, 3, 4, 5))
                cases += 1
        self.assertEqual(cases, 820)

    def test_seeded_small_products_against_choice_enumeration(self):
        rng = random.Random(20261018)
        for _ in range(120):
            choices = [(rng.randrange(21), rng.randrange(21)) for _ in range(rng.randrange(9))]
            target = rng.randrange(sum(max(pair) for pair in choices) + 3)
            self.check_product(choices, target, (1, 2, 7, 11))

    def test_main_gap_separate_witnesses_are_not_one_common_witness(self):
        choices, target = [(1, 6), (0, 36), (0, 36), (0, 36)], 36
        expansion, words = independent_expansion(choices)
        self.assertEqual(dict(sorted(expansion.items())),
                         {1: 1, 6: 1, 37: 3, 42: 3, 73: 3, 78: 3, 109: 1, 114: 1})
        self.assertEqual(sum(expansion.values()), 16)
        expected_counts = {2: 8, 3: 8, 5: 2, 7: 4}
        for modulus, coefficient in expected_counts.items():
            query = build_coefficient_proof(choices, target, modulus=modulus)
            self.assertEqual(query["target_coefficient"], coefficient)
            self.assertTrue(query["attainable"])
            witness = query["witness"]
            self.assertEqual(witness["total_weight"], 6 if modulus in (2, 3) else 1)
            self.assertFalse(verify_choice_witness(choices, target, witness)["valid"])
        joint = joint_residue_proof(choices, target, [2, 3, 5, 7])
        self.assertEqual(joint["joint_modulus"], 210)
        self.assertGreater(210, max(expansion))
        self.assertEqual(joint["query"]["status"], "EXACT")
        self.assertEqual(joint["query"]["target_coefficient"], 0)
        self.assertFalse(any(all((weight - target) % m == 0 for m in (2, 3, 5, 7)) for weight in words))

    def test_joint_lcm_non_coprime_repeated_and_empty_moduli(self):
        choices, target = [(0, 2), (1, 4), (0, 7)], 9
        expansion, _ = independent_expansion(choices)
        for moduli in ([4, 6], [4, 6, 4, 1], [], [1]):
            query = joint_residue_proof(choices, target, moduli)
            self.assertEqual(query["joint_modulus"], lcm(*moduli))
            expected = sum(count for weight, count in expansion.items()
                           if all((weight - target) % m == 0 for m in moduli))
            self.assertEqual(query["query"]["target_coefficient"], expected)
        self.assertEqual(joint_residue_proof(choices, target, [4, 6])["joint_modulus"], 12)

    def test_multiplicities_equal_choices_and_empty_product(self):
        choices = [(0, 0)] * 512
        query = build_coefficient_proof(choices, 0)
        self.assertEqual(query["target_coefficient"], 1 << 512)
        self.assertEqual(query["stats"]["peak_coefficient_bits"], 513)
        self.assertEqual(query["stats"]["peak_layer_states"], 1)
        self.assertTrue(verify_coefficient_proof(choices, 0, query["certificate"])["valid"])
        for target, modulus, expected in ((0, None, 1), (1, None, 0), (3, 3, 1), (1, 3, 0)):
            result = build_coefficient_proof([], target, modulus=modulus, max_transitions=0)
            self.assertEqual(result["target_coefficient"], expected)
            self.assertTrue(verify_coefficient_proof([], target, result["certificate"], modulus=modulus, max_transitions=0)["valid"])

    def test_exact_budget_boundaries_and_no_unknown_final_claim(self):
        choices, target = [(0, 1), (0, 3), (0, 5)], 4
        baseline = build_coefficient_proof(choices, target)
        limits = {"max_states": 8, "max_total_states": 15, "max_transitions": 14}
        self.assertEqual(baseline["stats"]["states_created"], 15)
        self.assertEqual(baseline["stats"]["transitions"], 14)
        self.assertEqual(build_coefficient_proof(choices, target, **limits)["status"], "EXACT")
        self.assertTrue(verify_coefficient_proof(choices, target, baseline["certificate"], **limits)["valid"])
        for name in limits:
            insufficient = {**limits, name: limits[name] - 1}
            result = build_coefficient_proof(choices, target, **insufficient)
            self.assertEqual(result["status"], "UNKNOWN")
            for key in ("target_coefficient", "attainable", "witness", "certificate"):
                self.assertIsNone(result[key])
            self.assertLessEqual(result["stats"]["states_created"], insufficient["max_total_states"])
            self.assertLessEqual(result["stats"]["peak_layer_states"], insufficient["max_states"])
            self.assertLessEqual(result["stats"]["transitions"], insufficient["max_transitions"])
            verified = verify_coefficient_proof(choices, target, baseline["certificate"], **insufficient)
            self.assertFalse(verified["valid"])
            self.assertEqual(verified["status"], "UNKNOWN")
            self.assertNotIn("target_coefficient", verified)

    def test_original_input_binding_recomputed_mutation_still_fails(self):
        choices, target, modulus = [(1, 6), (0, 36)], 36, 5
        result = build_coefficient_proof(choices, target, modulus=modulus)
        certificate = result["certificate"]
        for changed_choices, changed_target, changed_modulus in (
                ([(1, 7), (0, 36)], target, modulus),
                (choices, target + 1, modulus), (choices, target, 7)):
            self.assertFalse(verify_coefficient_proof(changed_choices, changed_target, certificate, modulus=changed_modulus)["valid"])
        forged = deepcopy(certificate)
        altered = [(1, 7), (0, 36)]
        forged["input_sha256"] = certificate_binding(altered, target, modulus)
        verdict = verify_coefficient_proof(altered, target, forged, modulus=modulus)
        self.assertEqual(verdict["status"], "INVALID")
        self.assertIn("recurrence", verdict["errors"][0])

    def test_malformed_counts_missing_states_and_false_witnesses_fail(self):
        choices, target = [(0, 1), (0, 2)], 3
        original = build_coefficient_proof(choices, target)["certificate"]
        mutations = []
        for mutate in (
                lambda c: c["layers"][0].__setitem__(0, [0, 2]),
                lambda c: c["layers"][1].pop(),
                lambda c: c["layers"][1].append([1, 1]),
                lambda c: c["layers"][1].__setitem__(0, [0, 0]),
                lambda c: c["layers"][1].__setitem__(0, [0, -1]),
                lambda c: c["layers"][1].__setitem__(0, [0, True]),
                lambda c: c["layers"][1].__setitem__(0, [0, 2]),
                lambda c: c.__setitem__("target_coefficient", 0),
                lambda c: c.__setitem__("witness", None),
                lambda c: c["witness"].__setitem__("bits", [0, 0]),
                lambda c: c["witness"].__setitem__("total_weight", 99),
                lambda c: c.__setitem__("mode", "cyclic"),
                lambda c: c.__setitem__("extra", True)):
            forged = deepcopy(original)
            mutate(forged)
            mutations.append(forged)
        mutations += [None, {}]
        for certificate in mutations:
            self.assertFalse(verify_coefficient_proof(choices, target, certificate)["valid"])
        zero = build_coefficient_proof(choices, 10)["certificate"]
        zero["witness"] = {"bits": [0, 0], "total_weight": 0}
        self.assertFalse(verify_coefficient_proof(choices, 10, zero)["valid"])

    def test_large_binary_exponents_do_not_use_decimal_conversion(self):
        large = 1 << 15000
        choices = [(0, large), (0, 1)]
        for modulus in (None, large + 3):
            result = build_coefficient_proof(choices, large + 1, modulus=modulus)
            self.assertEqual(result["target_coefficient"], 1)
            self.assertEqual(result["input_sha256"], certificate_binding(choices, large + 1, modulus))
            self.assertTrue(verify_coefficient_proof(choices, large + 1, result["certificate"], modulus=modulus)["valid"])
            self.assertEqual(result["witness"]["total_weight"], large + 1)

    def test_input_validation_and_json_replay(self):
        for choices, target, modulus in (([(0, -1)], 0, None), ([(0, True)], 0, None),
                                          ([(0, 1.0)], 0, None), ([(0,)], 0, None),
                                          ([], -1, None), ([], True, None),
                                          ([], 0, 0), ([], 0, True), ([], 0, 1.5)):
            with self.assertRaises(ValueError):
                build_coefficient_proof(choices, target, modulus=modulus)
            self.assertEqual(verify_coefficient_proof(choices, target, {}, modulus=modulus)["status"], "INVALID")
        with self.assertRaises(ValueError):
            joint_residue_proof([], 0, [0])
        for limits in ({"max_states": 0}, {"max_total_states": True}, {"max_transitions": -1}):
            with self.assertRaises(ValueError):
                build_coefficient_proof([], 0, **limits)
        choices = [(0, 2), (1, 4)]
        certificate = build_coefficient_proof(choices, 4, modulus=3)["certificate"]
        replay = json.loads(json.dumps(certificate))
        self.assertTrue(verify_coefficient_proof(choices, 4, replay, modulus=3)["valid"])

    def test_small_residues_can_complete_while_joint_table_hits_cap(self):
        choices = [(0, 1 << i) for i in range(16)]
        target = (1 << 16) - 1
        limits = {"max_states": 128, "max_total_states": 10000, "max_transitions": 100000}
        for modulus in (17, 19, 23):
            result = build_coefficient_proof(choices, target, modulus=modulus, **limits)
            self.assertEqual(result["status"], "EXACT")
        joint = joint_residue_proof(choices, target, [17, 19, 23], **limits)
        self.assertEqual(joint["joint_modulus"], 7429)
        self.assertEqual(joint["query"]["status"], "UNKNOWN")
        # These are easy positive instances; an independent explicit witness
        # prevents a state-cap failure being presented as hardness or UNSAT.
        witness = {"bits": [1] * 16, "total_weight": target}
        self.assertTrue(verify_choice_witness(choices, target, witness)["valid"])

    def test_saved_examples_current_hashes_and_all_certificates(self):
        here = Path(__file__).resolve().parent
        artifact = here / "RESULTS.json"
        if not artifact.exists():
            self.skipTest("saved experiment has not been generated")
        saved = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertTrue(saved["source_unchanged_during_run"])
        for name, expected in saved["source_sha256"].items():
            self.assertEqual(sha256((here / name).read_bytes()).hexdigest(), expected)
        for case in saved["cases"]:
            for query in case["queries"]:
                result = query["result"]
                if result["status"] == "EXACT":
                    self.assertTrue(verify_coefficient_proof(case["choices"], case["target"],
                                                            result["certificate"], modulus=query["modulus"],
                                                            **saved["verification_limits"])["valid"])
                else:
                    self.assertEqual(result["status"], "UNKNOWN")
                    for key in ("target_coefficient", "attainable", "witness", "certificate"):
                        self.assertIsNone(result[key])


if __name__ == "__main__":
    unittest.main()
