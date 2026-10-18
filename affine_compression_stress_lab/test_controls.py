import copy
import unittest

from controls import fixed_controls, parity_control, pigeonhole_control, verify_control


def exhaustive(case):
    return sum(all(any(bool(word >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause)
                   for clause in case['clauses']) for word in range(1 << case['n']))


class StressControlTests(unittest.TestCase):
    def test_original_small_truth_counts(self):
        for v in (4, 6, 8):
            for charge in (0, 1):
                for shuffled in (False, True):
                    case = parity_control(v, charge, 20261018+v, shuffled)
                    self.assertEqual(exhaustive(case), verify_control(case)['count'])
        for h in (1, 2, 3):
            for p in (h, h+1):
                case = pigeonhole_control(p, h)
                self.assertEqual(exhaustive(case), verify_control(case)['count'])

    def test_every_frozen_source_structure(self):
        self.assertEqual(len(fixed_controls()), 22)
        for case in fixed_controls():
            self.assertTrue(verify_control(case)['valid'])

    def test_original_clause_and_structure_tampering(self):
        for case in [parity_control(8, 0, 42), pigeonhole_control(4, 3)]:
            bad = copy.deepcopy(case); bad['clauses'].pop()
            with self.assertRaises(AssertionError): verify_control(bad)
            bad = copy.deepcopy(case); bad['expected_count'] += 1
            with self.assertRaises(AssertionError): verify_control(bad)
        bad = parity_control(8, 0, 42); bad['charges'][0] ^= 1
        with self.assertRaises(AssertionError): verify_control(bad)


if __name__ == '__main__':
    unittest.main()
