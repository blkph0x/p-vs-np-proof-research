import unittest


def clause_satisfied(clause, assignment):
    return any(((assignment >> (abs(lit) - 1)) & 1) == (lit > 0) for lit in clause)


def g_satisfies(variables, clauses, assignment):
    return all(clause_satisfied(clause, assignment) for clause in clauses)


def residual(variables, clauses, selector):
    """Suffix truth set for F(z,y)=G(y) AND NOT z after the z cut."""
    out = []
    for suffix in range(1 << variables):
        if selector == 1:
            continue
        if g_satisfies(variables, clauses, suffix):
            out.append(suffix)
    return tuple(out)


class ResidualEquivalenceReductionTests(unittest.TestCase):
    def assert_reduction(self, variables, clauses, unsat):
        zero = residual(variables, clauses, 0)
        one = residual(variables, clauses, 1)
        self.assertEqual((zero == one), unsat)
        self.assertEqual(bool(zero), not unsat)

    def test_satisfiable_controls_have_distinct_residuals(self):
        self.assert_reduction(1, [[1]], False)
        self.assert_reduction(2, [[1, 2], [-1, 2]], False)

    def test_unsatisfiable_controls_have_equal_dead_residuals(self):
        self.assert_reduction(1, [[1], [-1]], True)
        self.assert_reduction(2, [[1], [-1, 2], [-2]], True)

    def test_reduction_does_not_depend_on_clause_width(self):
        # A satisfiable 3-CNF and an unsatisfiable 3-CNF share the same selector gadget.
        self.assert_reduction(3, [[1, 2, 3], [-1, -2, 3]], False)
        self.assert_reduction(3, [[1, 2, 3], [-1], [-2], [-3]], True)


if __name__ == "__main__":
    unittest.main()
