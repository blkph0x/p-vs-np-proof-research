import copy
import itertools
import json
from pathlib import Path
import random
import unittest

from affine_hull import recover, compile_outside, canonical_equations
from review_affine_hull import verify, verify_saved, HullVerificationError
from run_affine_hull import cases, source_hashes


def projected_points(m, q, clauses):
    members = set()
    for values in itertools.product((False, True), repeat=m+q):
        if all(any(values[abs(lit)-1] == (lit > 0) for lit in row) for row in clauses):
            members.add(sum(1 << i for i in range(m) if values[i]))
    return members


def explicit_hull(members):
    if not members:
        return set()
    base = min(members)
    span = {0}
    for point in members:
        delta = point ^ base
        span |= {x ^ delta for x in list(span)}
    return {x ^ base for x in span}


def equation_points(m, equations):
    return {x for x in range(1 << m)
            if all((mask & x).bit_count() % 2 == rhs for mask, rhs in equations)}


class HullCertificateTests(unittest.TestCase):
    def test_all_256_visible_relations_match_independent_explicit_hull(self):
        for relation in range(256):
            clauses = [[-(i+1) if point & (1 << i) else i+1 for i in range(3)]
                       for point in range(8) if not relation & (1 << point)]
            result = recover(3, 0, clauses)
            checked = verify(3, 0, clauses, result)
            self.assertNotEqual(checked["status"], "UNKNOWN")
            expected = explicit_hull({x for x in range(8) if relation & (1 << x)})
            self.assertEqual(equation_points(3, result["equations"]), expected)
            self.assertLessEqual(len(result["queries"]), 4)

    def test_100_projected_cnfs_with_hidden_variables(self):
        rng = random.Random(20261020)
        for _ in range(100):
            m, q = rng.randrange(4), rng.randrange(3)
            n = m + q
            clauses = []
            for _ in range(rng.randrange(9)):
                support = rng.sample(range(n), rng.randrange(min(n, 3)+1))
                clauses.append([rng.choice((-1, 1))*(v+1) for v in support])
            result = recover(m, q, clauses)
            self.assertTrue(verify(m, q, clauses, result)["status"].startswith("VERIFIED"))
            self.assertEqual(equation_points(m, result["equations"]),
                             explicit_hull(projected_points(m, q, clauses)))

    def test_hull_is_not_promoted_to_projection_or_counting_equality(self):
        hole = [[-1, -2]]
        cert = recover(2, 0, hole)
        self.assertEqual(cert["equations"], [])
        self.assertNotEqual(projected_points(2, 0, hole), equation_points(2, []))
        self.assertEqual(verify(2, 0, hole, cert)["projection_affinity"], "NOT_CHECKED")
        counts = [sum(all(any(values[abs(lit)-1] == (lit > 0) for lit in row)
                          for row in [[1, 2]]) for values in [(x, False), (x, True)])
                  for x in (False, True)]
        self.assertEqual(counts, [1, 2])

    def test_outside_compilation_preserves_each_visible_assignment(self):
        for members in ({0}, {1, 2}, {0, 3}, {1, 2, 4}, set(range(8))):
            equations, _ = canonical_equations(3, sorted(members))
            nvars, cnf = compile_outside(3, [], equations)
            actual = projected_points(3, nvars-3, cnf)
            self.assertEqual(actual, set(range(8))-explicit_hull(members))

    def test_saved_inputs_hashes_and_certificate_replay(self):
        saved = json.loads(Path(__file__).with_name("HULL_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual(verify_saved(saved)["status"], "VERIFIED")
        self.assertEqual(saved["source_sha256"], source_hashes())
        expected = cases()
        self.assertEqual(len(saved["cases"]), len(expected))
        for row, (name, m, q, clauses, caps) in zip(saved["cases"], expected):
            self.assertEqual(row["name"], name)
            self.assertEqual(row["source"], {"visible_width": m, "hidden_width": q, "clauses": clauses})
            self.assertEqual(row["caps"], caps)
            verify(m, q, clauses, row["certificate"])
            self.assertLessEqual(row["certificate"]["solver_totals"]["decisions"],
                                 caps.get("max_decisions", 1000))

    def test_mutated_terminal_resolution_and_missing_proof_are_rejected(self):
        clauses = [[-1, 2], [-1, -2]]
        good = json.loads(json.dumps(recover(1, 1, clauses)))
        self.assertEqual(good["status"], "EXACT_HULL")
        self.assertEqual(good["dimension"], 0)
        self.assertEqual(good["queries"][-1]["result"]["status"], "UNSAT")
        mutations = []
        missing = copy.deepcopy(good); missing["queries"][-1]["result"]["proof"] = []; mutations.append(missing)
        bad = copy.deepcopy(good); bad["queries"][-1]["result"]["proof"][-1]["derivation"][-1]["result"] = [1]; mutations.append(bad)
        bad = copy.deepcopy(good); bad["queries"][-1]["clauses"].pop(); mutations.append(bad)
        bad = copy.deepcopy(good); bad["equations"] = []; mutations.append(bad)
        bad = copy.deepcopy(good); bad["source"]["clauses"] = []; mutations.append(bad)
        bad = copy.deepcopy(good); bad["queries"][0]["result"]["model"]["0"] = True; mutations.append(bad)
        bad = copy.deepcopy(good); bad["queries"].pop(); mutations.append(bad)
        for index, corrupt in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(HullVerificationError):
                verify(1, 1, clauses, corrupt)

    def test_caps_never_certify_partial_hulls(self):
        for caps in ({"max_decisions": 0}, {"max_calls": 0}, {"max_calls": 1},
                     {"max_input_vars": 1}, {"max_input_clauses": 0}):
            clauses = [[1, 2]]
            result = recover(2, 0, clauses, **caps)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertEqual(verify(2, 0, clauses, result)["status"], "UNKNOWN")
            forged = copy.deepcopy(result)
            forged["status"], forged["equations"], forged["dimension"] = "EXACT_HULL", [], 2
            with self.assertRaises(HullVerificationError):
                verify(2, 0, clauses, forged)

    def test_trust_does_not_depend_on_stats_or_python_assertions(self):
        result = recover(2, 0, [[1]])
        forged = copy.deepcopy(result)
        forged["queries"][-1]["result"]["stats"]["resolution_steps"] += 1
        with self.assertRaises(HullVerificationError):
            verify(2, 0, [[1]], forged)
        malformed = copy.deepcopy(result)
        malformed["queries"][0]["result"]["model"]["unexpected"] = True
        with self.assertRaises(HullVerificationError):
            verify(2, 0, [[1]], malformed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
