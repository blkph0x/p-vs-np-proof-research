"""Correctness and cap controls for the general proof-producing CDCL solver."""
import json
from itertools import combinations, product
from pathlib import Path
import random
import unittest

from cdcl import CDCL, normalize_clause


HERE = Path(__file__).resolve().parent


def direct(nvars, clauses):
    return any(all(any((assignment[abs(lit) - 1] == (lit > 0))
                       for lit in clause) for clause in clauses)
               for assignment in product((False, True), repeat=nvars))


def pigeonhole(pigeons, holes):
    variables = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = []
    for pigeon in range(pigeons):
        clauses.append(tuple(variables(pigeon, hole) for hole in range(holes)))
    for pigeon in range(pigeons):
        for left, right in combinations(range(holes), 2):
            clauses.append((-variables(pigeon, left), -variables(pigeon, right)))
    for hole in range(holes):
        for left, right in combinations(range(pigeons), 2):
            clauses.append((-variables(left, hole), -variables(right, hole)))
    return pigeons * holes, tuple(clauses)


class CDCLTests(unittest.TestCase):
    def test_normalization_and_input_validation(self):
        self.assertEqual(normalize_clause([2, 1, 1]), (1, 2))
        self.assertIsNone(normalize_clause([1, -1, 2]))
        with self.assertRaises(ValueError):
            CDCL(1, ((0,),))
        with self.assertRaises(ValueError):
            CDCL(1, ((2,),))

    def test_small_formula_exhaustive(self):
        pool = tuple((lit,) for lit in (1, -1, 2, -2, 3, -3))
        pool += ((1, 2), (1, -2), (-1, 2), (-1, -2),
                 (1, 3), (1, -3), (-1, 3), (-1, -3),
                 (2, 3), (2, -3), (-2, 3), (-2, -3))
        for size in range(4):
            for clauses in combinations(pool, size):
                result = CDCL(3, clauses).solve()
                expected = direct(3, clauses)
                self.assertEqual(result["status"], "SAT" if expected else "UNSAT")
                if expected:
                    self.assertIsNotNone(result["model"])

    def test_pigeonhole_unsat_has_resolution_trace(self):
        nvars, clauses = pigeonhole(3, 2)
        result = CDCL(nvars, clauses).solve()
        self.assertEqual(result["status"], "UNSAT")
        self.assertGreater(result["stats"]["conflicts"], 0)
        self.assertTrue(any(e["kind"] == "terminal-empty" for e in result["proof"]))

    def test_sat_model_and_parity_style_unsat(self):
        sat = CDCL(2, ((1, 2), (-1, 2))).solve()
        self.assertEqual(sat["status"], "SAT")
        self.assertTrue(direct(2, ((1, 2), (-1, 2))))
        clauses = tuple(tuple((v + 1) if not bit else -(v + 1)
                              for v, bit in enumerate(bits))
                        for bits in product((0, 1), repeat=3))
        result = CDCL(3, clauses).solve()
        self.assertEqual(result["status"], "UNSAT")

    def test_resource_cap_is_unknown(self):
        nvars, clauses = pigeonhole(4, 3)
        result = CDCL(nvars, clauses, max_decisions=0).solve()
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "DECISION_CAP")

    def test_seeded_random_three_sat_controls(self):
        rng = random.Random(20261019)
        pool = []
        for _ in range(200):
            width = rng.choice((1, 2, 3))
            variables = rng.sample(range(1, 6), width)
            pool.append(tuple(rng.choice((-1, 1)) * variable for variable in variables))
        for _ in range(300):
            clauses = tuple(rng.sample(pool, rng.randrange(10)))
            result = CDCL(5, clauses).solve()
            self.assertIn(result["status"], ("SAT", "UNSAT"))
            self.assertEqual(result["status"], "SAT" if direct(5, clauses) else "UNSAT")

    def test_saved_artifact_and_independent_review(self):
        artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_cases_match_direct"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["proofs_match"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
