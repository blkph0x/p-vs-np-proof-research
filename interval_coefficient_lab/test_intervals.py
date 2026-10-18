import copy
import itertools
import random
import unittest

from intervals import solve, verify, separated_blocks, separated_block_modular_witness


class IntervalTests(unittest.TestCase):
    def test_random_original_products(self):
        rng = random.Random(76251)
        for _ in range(500):
            pairs = [[rng.randrange(15), rng.randrange(15)] for _ in range(rng.randrange(10))]
            target = rng.randrange(100)
            reachable = {sum(pair[b] for pair, b in zip(pairs, bits))
                         for bits in itertools.product((0, 1), repeat=len(pairs))}
            proof = solve(pairs, target)
            check = verify(pairs, target, proof)
            self.assertEqual(check["status"], "VERIFIED")
            self.assertEqual(proof["feasible"], target in reachable)
            expanded = {v for lo, hi in proof["layers"][-1] for v in range(lo, hi+1)}
            self.assertEqual(expanded, {x for x in reachable if x <= target})

    def test_empty_and_zero(self):
        for pairs, target, answer in [([], 0, True), ([], 1, False), ([[0, 0]]*5, 0, True), ([[2, 4]], 1, False)]:
            proof = solve(pairs, target)
            self.assertEqual(proof["feasible"], answer)
            self.assertEqual(verify(pairs, target, proof)["status"], "VERIFIED")

    def test_huge_support_compresses(self):
        pairs, target = separated_blocks(256)
        proof = solve(pairs, target, max_intervals=1)
        self.assertFalse(proof["feasible"])
        check = verify(pairs, target, proof)
        self.assertEqual(check["support_size_at_most_target"], 1 << 256)
        self.assertEqual(check["peak_intervals"], 1)
        for modulus in [1, 2, 3, 97, target//2+1, target-1, target]:
            bits = separated_block_modular_witness(256, modulus)
            value = sum(pair[b] for pair, b in zip(pairs, bits))
            self.assertNotEqual(value, target)
            self.assertEqual(value % modulus, target % modulus)

    def test_all_small_moduli(self):
        for q in range(1, 8):
            pairs, target = separated_blocks(q)
            for modulus in range(1, target+1):
                bits = separated_block_modular_witness(q, modulus)
                self.assertEqual(sum(p[b] for p, b in zip(pairs, bits)) % modulus, target % modulus)

    def test_fragmentation_unknown(self):
        pairs = [[0, 4**i] for i in range(14)]
        target = sum(p[1] for p in pairs)
        proof = solve(pairs, target, max_intervals=32)
        self.assertEqual(proof["status"], "UNKNOWN")
        self.assertNotIn("feasible", proof)
        self.assertEqual(verify(pairs, target, proof)["status"], "UNKNOWN")

    def test_budget_boundaries(self):
        pairs, target = [[0, 1], [0, 2]], 3
        proof = solve(pairs, target, max_intervals=1, max_total_intervals=3, max_spans=4)
        self.assertEqual(proof["status"], "EXACT")
        self.assertEqual(verify(pairs, target, proof, max_total_intervals=2)["status"], "UNKNOWN")
        for kwargs in [{"max_intervals": 0}, {"max_total_intervals": 2}, {"max_spans": 3}]:
            self.assertEqual(solve(pairs, target, **kwargs)["status"], "UNKNOWN")

    def test_tampered_layers_and_witness(self):
        pairs, target = [[0, 1], [0, 3]], 4
        original = solve(pairs, target)
        variants = []
        altered = copy.deepcopy(original); altered["layers"][1][0][1] = 2; variants.append(altered)
        altered = copy.deepcopy(original); altered["layers"][-1] = [[0, 4]]; variants.append(altered)
        altered = copy.deepcopy(original); altered["witness"] = [0, 0]; variants.append(altered)
        altered = copy.deepcopy(original); altered["feasible"] = 1; variants.append(altered)
        altered = copy.deepcopy(original); altered["stats"]["generated_spans"] += 1; variants.append(altered)
        for altered in variants:
            self.assertEqual(verify(pairs, target, altered)["status"], "INVALID")
        self.assertEqual(verify([[0, 2], [0, 3]], target, original)["status"], "INVALID")

    def test_malformed_inputs(self):
        for pairs, target in [([[False, 1]], 1), ([[0, -1]], 1), ([[0, 1, 2]], 1), ([], True), ([], -1)]:
            with self.assertRaises(ValueError):
                solve(pairs, target)
        with self.assertRaises(ValueError):
            solve([], 0, max_intervals=True)

    def test_large_integer_hash(self):
        value = 1 << 15000
        proof = solve([[0, value]], value)
        self.assertEqual(verify([[0, value]], value, proof)["status"], "VERIFIED")
        self.assertEqual(verify([[0, value+1]], value, proof)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
