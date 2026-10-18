import itertools
import copy
import unittest

import engine
from cdcl import CDCLMixed, solve_encoded
import polymorphism
from review_cdcl import replay_solver


class TestHornCdclt(unittest.TestCase):
    def test_h_relation_is_exact(self):
        accepted = []
        clauses = engine.h_clauses(1, 2, 3)
        for bits in itertools.product((0, 1), repeat=3):
            ok = all(any((lit > 0) == bool(bits[abs(lit) - 1]) for lit in c)
                     for c in clauses)
            if ok:
                accepted.append(bits)
        self.assertEqual(set(accepted), {(0, 0, 0), (1, 1, 0), (0, 0, 1)})

    def test_a_relation_is_exact(self):
        accepted = []
        for y, w, z0, z1 in itertools.product((0, 1), repeat=4):
            if (y ^ z1) == 0 and (w ^ z0 ^ z1) == 1:
                accepted.append((y, w, z0, z1))
        self.assertEqual(set(accepted), {(0, 1, 0, 0), (0, 0, 1, 0),
                                         (1, 0, 0, 1), (1, 1, 1, 1)})

    def test_gadget_projection_is_exact_one(self):
        table = engine.gadget_projection_table()
        for target, witnesses in table.items():
            self.assertEqual(bool(witnesses), sum(target) == 1, target)

    def test_horn_certificate_replay(self):
        theory = engine.HornTheory([(-1, 2), (1, -2), (-1, -2, -3)])
        props, conflict = theory.analyze({0: True, 1: True})
        self.assertIsNone(conflict)
        self.assertEqual(props[0][:2], (2, False))
        self.assertTrue(theory.verify(props[0][2]))
        _, conflict = theory.analyze({0: True, 1: True, 2: True})
        self.assertIsNotNone(conflict)
        self.assertTrue(theory.verify(conflict))

    def test_horn_rejects_non_horn(self):
        with self.assertRaises(ValueError):
            engine.HornTheory([(1, 2)])

    def test_horn_rejects_forged_certificate(self):
        theory = engine.HornTheory([(-1, 2), (1, -2), (-1, -2, -3)])
        props, _ = theory.analyze({0: True, 1: True})
        cert = dict(props[0][2])
        cert["lit"] = 3
        self.assertFalse(theory.verify(cert))

    def test_affine_certificate_replay(self):
        theory = engine.AffineTheory([((1 << 0) | (1 << 1), 0)])
        props, conflict = theory.analyze({0: True})
        self.assertIsNone(conflict)
        self.assertEqual(props[0][:2], (1, True))
        self.assertTrue(theory.verify(props[0][2]))
        _, conflict = theory.analyze({0: True, 1: False})
        self.assertIsNotNone(conflict)
        self.assertTrue(theory.verify(conflict))

    def test_affine_rejects_forged_certificate(self):
        theory = engine.AffineTheory([((1 << 0) | (1 << 1), 0)])
        props, _ = theory.analyze({0: True})
        cert = dict(props[0][2])
        cert["value"] = not cert["value"]
        self.assertFalse(theory.verify(cert))
        cert["value"] = props[0][2]["value"]
        cert["combo"] = -1
        self.assertFalse(theory.verify(cert))

    def test_single_gadget_solver_matches_direct(self):
        for target in itertools.product((0, 1), repeat=3):
            # Add units by fixing target variables in the initial assignment.
            clauses = [(1, 2, 3)]
            n, horn, affine = engine.encode_exact_one(clauses)
            result = engine.MixedPortfolioSolver(n, horn=horn, affine=affine).solve(
                {i: bool(target[i]) for i in range(3)})
            self.assertEqual(result is not None, sum(target) == 1, target)

    def test_encoded_formula_matches_direct_on_small_corpus(self):
        candidates = [
            [(1, 2, 3)],
            [(1, 2, 3), (1, 2, 4)],
            [(1, 2, 3), (1, 3, 4)],
            [(1, 2, 3), (2, 3, 4)],
            [(1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4)],
        ]
        for clauses in candidates:
            direct = engine.direct_exact_one_sat(clauses)
            encoded = engine.encoded_sat(clauses)
            self.assertEqual(encoded is not None, direct is not None, clauses)
            if encoded is not None:
                for clause in clauses:
                    self.assertEqual(sum(encoded[v - 1] for v in clause), 1)

    def test_complete_triples_are_unsat(self):
        clauses = engine.all_triples(4)
        self.assertIsNone(engine.direct_exact_one_sat(clauses))
        n, horn, affine = engine.encode_exact_one(clauses)
        solver = engine.MixedPortfolioSolver(n, horn=horn, affine=affine)
        self.assertIsNone(solver.solve())
        self.assertGreater(solver.stats["nodes"], 1)
        self.assertEqual(solver.stats["certificates_verified"],
                         len(solver.certificates))

    def test_cdcl_matches_direct_and_replays(self):
        cases = [
            [(1, 2, 3)],
            [(1, 2, 3), (1, 2, 4)],
            [(1, 2, 3), (1, 3, 4)],
            engine.all_triples(4),
            engine.all_triples(5),
        ]
        for clauses in cases:
            solver, result = solve_encoded(clauses)
            self.assertEqual(result is not None,
                             engine.direct_exact_one_sat(clauses) is not None)
            self.assertTrue(replay_solver(solver)["all_events_valid"])
            self.assertTrue(replay_solver(solver)["database_size_matches"])
            if result is not None:
                self.assertTrue(all(sum(result[v - 1] for v in c) == 1 for c in clauses))

    def test_cdcl_learning_is_visible(self):
        solver, result = solve_encoded(engine.all_triples(4))
        self.assertIsNone(result)
        self.assertGreater(solver.stats["learned_clauses"], 0)
        self.assertGreater(solver.stats["resolution_steps"], 0)
        review = replay_solver(solver)
        self.assertTrue(review["all_events_valid"])
        self.assertTrue(review["database_size_matches"])

    def test_cdcl_forged_resolution_is_rejected(self):
        solver, _ = solve_encoded(engine.all_triples(4))
        forged = copy.deepcopy(solver)
        event = next(e for e in forged.proof if e.get("kind") == "resolve")
        event["result"] = tuple(reversed(event["result"]))
        self.assertFalse(replay_solver(forged)["all_events_valid"])

    def test_cdcl_fixed_target_units_match_gadget(self):
        n, horn, affine = engine.encode_exact_one([(1, 2, 3)])
        for target in itertools.product((False, True), repeat=3):
            units = [(i + 1 if target[i] else -(i + 1),) for i in range(3)]
            solver = CDCLMixed(n, horn=horn, affine=affine, initial_clauses=units)
            result = solver.solve()
            self.assertEqual(result is not None, sum(target) == 1, target)
            self.assertTrue(replay_solver(solver)["all_events_valid"])

    def test_invalid_exact_one_clause_rejected(self):
        with self.assertRaises(ValueError):
            engine.encode_exact_one([(1, 1, 2)])
        with self.assertRaises(ValueError):
            engine.encode_exact_one([(0, 1, 2)])

    def test_common_polymorphisms_are_only_projections_up_to_arity_four(self):
        for arity in range(1, 5):
            common = polymorphism.common_operations(arity)
            projections = [polymorphism.projection_table(arity, i)
                           for i in range(arity)]
            self.assertEqual(sorted(common), sorted(projections))

    def test_named_schaefer_operations_are_separated(self):
        matrix = polymorphism.named_preservation_matrix()
        self.assertTrue(matrix["AND"]["preserves_H"])
        self.assertFalse(matrix["AND"]["preserves_A"])
        self.assertTrue(matrix["MINORITY_XOR"]["preserves_A"])
        self.assertFalse(matrix["MINORITY_XOR"]["preserves_H"])
        self.assertFalse(matrix["MAJORITY"]["preserves_A"])

    def test_polymorphism_artifact_replay(self):
        self.assertEqual(polymorphism.common_operations(1), [2])
        self.assertEqual(polymorphism.common_operations(2), [10, 12])
        self.assertEqual(polymorphism.common_operations(3), [170, 204, 240])

    def test_all_arity_affine_candidates_reduce_to_singletons(self):
        for arity in range(1, 13):
            candidates = polymorphism.affine_common_candidates(arity)
            self.assertEqual(len(candidates), arity)
            self.assertTrue(all(constant == 0 and support.bit_count() == 1
                                for constant, support, _ in candidates))


if __name__ == "__main__":
    unittest.main(verbosity=2)
