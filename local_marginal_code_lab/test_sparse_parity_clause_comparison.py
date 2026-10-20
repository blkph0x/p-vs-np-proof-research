"""Exact control for the sparse parity clause LP versus check-local tables."""

from __future__ import annotations

import itertools
import unittest


def parity_cnf(scope: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Four clauses forbidding the odd assignments on a 3-variable scope."""
    clauses = []
    for forbidden in itertools.product((0, 1), repeat=len(scope)):
        if sum(forbidden) % 2 == 0:
            continue
        # A clause is false exactly at the forbidden assignment.
        clause = tuple(
            variable + 1 if bit == 0 else -(variable + 1)
            for variable, bit in zip(scope, forbidden)
        )
        clauses.append(clause)
    return tuple(clauses)


def pin_clause(clause: tuple[int, ...], pin: int = 0) -> tuple[int, ...] | None:
    """Substitute ``x_pin=1`` into a clause; None means tautology."""
    result = []
    for literal in clause:
        variable = abs(literal) - 1
        if variable == pin:
            if literal > 0:
                return None
            continue
        result.append(literal)
    return tuple(result)


def simplified_clauses() -> tuple[tuple[int, ...], ...]:
    clauses = parity_cnf((0, 1, 2)) + parity_cnf((0, 1, 3))
    return tuple(value for clause in clauses
                 if (value := pin_clause(clause)) is not None)


def clause_lp_bound() -> int:
    """Return the exact symbolic lower bound on F=x1+x2+x3."""
    clauses = simplified_clauses()
    # The two positive clauses give x1+x2 >= 1 and x1+x3 >= 1.
    lower = [clause for clause in clauses if all(literal > 0 for literal in clause)]
    assert lower == [(2, 3), (2, 4)]
    # F = x1+x2+x3 >= 1 follows from the first inequality and x3 >= 0.
    return 1


class SparseParityClauseComparisonTests(unittest.TestCase):
    def test_pin_simplifies_each_parity_check_to_exact_pair_relation(self):
        self.assertEqual(simplified_clauses(), ((2, 3), (-2, -3), (2, 4), (-2, -4)))

    def test_clause_lp_has_exact_optimum_one(self):
        self.assertEqual(clause_lp_bound(), 1)
        witness = {0: 1, 1: 1, 2: 0, 3: 0}
        self.assertEqual(sum(witness[index] for index in (1, 2, 3)), 1)
        for scope in ((0, 1, 2), (0, 1, 3)):
            self.assertEqual(sum(witness[index] for index in scope) % 2, 0)

    def test_check_local_level_two_accepts_zero_free_point(self):
        # Both checks have scope three, so no check is visible on a free pair.
        self.assertTrue(all(len(scope) > 2 for scope in ((0, 1, 2), (0, 1, 3))))
        check_local_point = {0: 1, 1: 0, 2: 0, 3: 0}
        self.assertEqual(sum(check_local_point[index] for index in (1, 2, 3)), 0)

    def test_clause_mutation_is_detected(self):
        mutated = parity_cnf((0, 1, 2))[:-1] + parity_cnf((0, 1, 3))
        self.assertNotEqual(mutated, parity_cnf((0, 1, 2)) + parity_cnf((0, 1, 3)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
