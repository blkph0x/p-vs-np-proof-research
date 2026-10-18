import unittest

from exact_oracle import (apply, exact_optimum, exact_parameter_optimum,
                          exceptional_stats, rank, score, transforms, verify_exact)


class ExactRowBasisTests(unittest.TestCase):
    def test_gl_counts(self):
        self.assertEqual(sum(1 for _ in transforms(0)), 1)
        self.assertEqual(sum(1 for _ in transforms(3)), 168)
        self.assertEqual(sum(1 for _ in transforms(4)), 20160)

    def test_transform_and_score(self):
        rows = (0b0011, 0b0101, 0b1110)
        transform = (1, 2, 4)
        self.assertEqual(rank(transform), 3)
        changed = apply(rows, transform)
        self.assertEqual(changed, rows)
        self.assertEqual(score(changed, 4), (0, 0, 7))

    def test_exact_certificate_and_mutation(self):
        rows = (0b0011, 0b0101, 0b1110)
        result = exact_optimum(rows, 4)
        self.assertEqual(result['status'], 'EXACT')
        self.assertTrue(verify_exact(rows, 4, result)['valid'])
        changed = dict(result); changed['objective'] = [0, 0, 0]
        self.assertFalse(verify_exact(rows, 4, changed)['valid'])

    def test_known_gl3_trap(self):
        counts = {1: 1, 2: 4, 3: 3, 4: 4, 5: 3, 6: 3, 7: 2}
        columns = [value for value, count in counts.items() for _ in range(count)]
        rows = tuple(sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
                     for i in range(3))
        result = exact_optimum(rows, len(columns))
        self.assertEqual(result['objective'][0], 1)

    def test_cap_is_unknown(self):
        result = exact_optimum((1, 2, 4, 8, 16), 5, max_transforms=1000)
        self.assertEqual(result['status'], 'UNKNOWN')

    def test_exception_rank_can_trade_against_exception_count(self):
        rows = (17719, 49139, 75762, 15854)
        q_result = exact_optimum(rows, 17)
        p_result = exact_parameter_optimum(rows, 17)
        self.assertEqual(q_result['objective'], [2, 2, 28])
        self.assertEqual(p_result['objective'], [1, 4, 4, 31])
        self.assertEqual(exceptional_stats(tuple(q_result['transformed_rows']), 17), (2, 2, 2, 28))
        self.assertEqual(exceptional_stats(tuple(p_result['transformed_rows']), 17), (4, 1, 4, 31))


if __name__ == '__main__':
    unittest.main()
