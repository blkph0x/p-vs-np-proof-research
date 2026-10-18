import unittest

from rank_aware_discovery import discover, objective, verify


class RankAwareDiscoveryTests(unittest.TestCase):
    def test_tradeoff_reaches_rank_one(self):
        rows = (17719, 49139, 75762, 15854)
        result = discover(rows, 17)
        self.assertEqual(result['objective'][0], 1)
        self.assertEqual(result['objective'], [1, 4, 4, 31])
        self.assertTrue(verify(rows, 17, result)['valid'])

    def test_rank_aware_objective_and_mutation(self):
        rows = (3, 5, 14)
        result = discover(rows, 4, max_restarts=0)
        self.assertEqual(result['objective'], list(objective(tuple(result['transformed_rows']), 4)))
        mutated = dict(result); mutated['objective'] = [0, 0, 0, 0]
        self.assertFalse(verify(rows, 4, mutated)['valid'])

    def test_budget_is_explicit(self):
        result = discover((1, 2, 4, 8, 16), 5, max_candidate_evaluations=1)
        self.assertEqual(result['termination'], 'EVALUATION_LIMIT')
        self.assertLessEqual(result['candidate_evaluations'], 1)


if __name__ == '__main__':
    unittest.main()
