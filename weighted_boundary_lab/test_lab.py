import copy
from fractions import Fraction
from itertools import product
import random
import unittest

from weighted_boundary import (direct_marginal, evaluate_summary, marginalize,
                               verify_marginal)


def request(boundary, internal, equations=(), phase=(), scalar=1):
    return {"schema": "weighted_affine_marginal_v1", "boundary": list(boundary),
            "internal": list(internal), "equations": [list(row) for row in equations],
            "phase": list(phase), "scalar": scalar}


class WeightedBoundaryTests(unittest.TestCase):
    def checked(self, net):
        result = marginalize(net)
        self.assertEqual(result["status"], "EXACT", result)
        self.assertTrue(verify_marginal(net, result)["valid"])
        for assignment in product((0, 1), repeat=len(net["boundary"])):
            self.assertEqual(evaluate_summary(result["summary"], assignment),
                             direct_marginal(net, assignment), assignment)
        return result

    def test_free_linear_phase_becomes_boundary_equation(self):
        # sum_t (-1)^(t*b) = 2*[b=0].
        result = self.checked(request(["b"], ["t"], phase=[3]))
        self.assertEqual(result["summary"]["scalar"], [2, 1])
        self.assertEqual(result["summary"]["equations"], [[1, 0]])
        self.assertEqual(result["summary"]["phase"], [])

    def test_internal_quadratic_pair_becomes_boundary_phase(self):
        # sum_(s,t) (-1)^(s*t+s*a+t*b) = 2*(-1)^(a*b).
        result = self.checked(request(["a", "b"], ["s", "t"], phase=[12, 5, 10]))
        self.assertEqual(result["summary"]["scalar"], [2, 1])
        self.assertEqual(result["summary"]["equations"], [])
        self.assertEqual(result["summary"]["phase"], [3])

    def test_pivot_substitution_preserves_quadratic_phase(self):
        # t=a+b and phase t*c, so the result is (-1)^(a*c+b*c).
        result = self.checked(request(["a", "b", "c"], ["t"],
                                       equations=[(11, 0)], phase=[12]))
        self.assertEqual(result["summary"]["scalar"], [1, 1])
        self.assertEqual(result["summary"]["equations"], [])
        self.assertEqual(result["summary"]["phase"], [5, 6])

    def test_inconsistent_free_phase_is_zero(self):
        result = self.checked(request([], ["t"], phase=[1]))
        self.assertEqual(result["summary"]["equations"], [[0, 1]])
        self.assertEqual(evaluate_summary(result["summary"], ()), Fraction(0))

    def test_dependent_equations_and_unused_internal(self):
        # Duplicate rows and a free, phase-independent bit are retained exactly.
        result = self.checked(request(["a"], ["t", "u"], equations=[(1, 0), (1, 0)], phase=[]))
        self.assertEqual(result["summary"]["scalar"], [4, 1])
        self.assertEqual(result["summary"]["equations"], [[1, 0]])
        self.assertEqual(result["summary"]["phase"], [])

    def test_seeded_small_instances_match_direct_oracle(self):
        rng = random.Random(20261018)
        for _ in range(180):
            k, m = rng.randrange(0, 4), rng.randrange(0, 4)
            n = k + m
            equations = [(rng.randrange(1 << n), rng.randrange(2)) for _ in range(rng.randrange(0, 5))]
            terms = [0] + [1 << i for i in range(n)]
            terms += [(1 << i) | (1 << j) for i in range(n) for j in range(i + 1, n)]
            phase = [term for term in terms if rng.randrange(2)]
            net = request([f"b{i}" for i in range(k)], [f"t{i}" for i in range(m)],
                          equations=equations, phase=phase,
                          scalar=[rng.choice((-3, -1, 1, 2)), rng.choice((1, 2, 5))])
            self.checked(net)

    def test_certificate_mutations_rejected(self):
        net = request(["a", "b"], ["s", "t"], phase=[12, 5, 10])
        result = self.checked(net)
        mutations = []
        altered = copy.deepcopy(result)
        altered["certificate"]["input_sha256"] = "0" * 64
        mutations.append(altered)
        altered = copy.deepcopy(result)
        altered["certificate"]["steps"][0]["variable"] = 99
        mutations.append(altered)
        altered = copy.deepcopy(result)
        altered["certificate"]["steps"][0]["kind"] = "pivot"
        altered["certificate"]["steps"][0]["pivot"] = [0, 0]
        mutations.append(altered)
        altered = copy.deepcopy(result)
        altered["summary"]["scalar"] = [99, 1]
        mutations.append(altered)
        altered = copy.deepcopy(result)
        altered["certificate"]["summary"]["phase"] = []
        mutations.append(altered)
        for mutation in mutations:
            self.assertFalse(verify_marginal(net, mutation)["valid"], mutation)

    def test_explicit_caps_return_unknown_without_partial_result(self):
        net = request(["a"], ["t"], phase=[3])
        result = marginalize(net, max_work=0)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["summary"])
        self.assertIsNone(result["certificate"])
        self.assertEqual(verify_marginal(net, result)["status"], "INVALID")

    def test_malformed_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            marginalize(request(["a", "a"], [], phase=[]))
        with self.assertRaises(ValueError):
            marginalize(request(["a"], [], phase=[7]))
        with self.assertRaises(ValueError):
            marginalize(request(["a"], [], equations=[(2, 0)]))


if __name__ == "__main__":
    unittest.main()
