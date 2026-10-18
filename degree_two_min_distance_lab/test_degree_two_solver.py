import unittest

import degree_two_solver as solver
from run_experiments import controls


class DegreeTwoSolverTests(unittest.TestCase):
    def test_controls_match_bruteforce(self):
        for control in controls():
            instance = solver.encode(control['rows'], control['columns'])
            solution = solver.solve(instance)
            best = None
            for selection in range(1, 1 << len(instance.columns)):
                if solver.syndrome(instance, [i for i in range(len(instance.columns))
                                               if selection >> i & 1]) == 0:
                    weight = selection.bit_count()
                    best = weight if best is None else min(best, weight)
            self.assertEqual(solution['distance'], best)
            self.assertTrue(solver.verify_solution(instance, solution))

    def test_weight_three_is_rejected(self):
        with self.assertRaises(ValueError):
            solver.encode(3, [0b111])


if __name__ == '__main__':
    unittest.main()
