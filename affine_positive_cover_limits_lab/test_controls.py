import unittest
from fractions import Fraction
import controls as c


class PositiveCoverTests(unittest.TestCase):
    def test_affine_enumerator_against_all_three_bit_subsets(self):
        expected=set()
        for support in range(1,256):
            words=[x for x in range(8) if support >> x & 1]
            anchor=words[0];linear={x^anchor for x in words}
            if all(x^y in linear for x in linear for y in linear):expected.add(support)
        actual=list(c.affine_supports(3))
        self.assertEqual(len(actual),len(set(actual)))
        self.assertEqual(set(actual),expected)
        self.assertEqual(len(actual),51)

    def test_support_bounds_and_local_minimum(self):
        rows=[c.supports_control(m) for m in range(3)]
        self.assertEqual([r['affine_supports'] for r in rows],[1,51,26387])
        self.assertEqual(rows[1]['maximum_two_support_union'],6)
        self.assertEqual(rows[2]['maximum_contained_size'],16)
        self.assertEqual(rows[2]['maximum_intersection_squared_over_size'],[2401,64])

    def test_constructive_identities_and_signed_scope(self):
        rows=[c.constructions_control(m) for m in range(5)]
        self.assertEqual(sum(r['original_assignments'] for r in rows),4681)
        signed=c.signed_controls()
        self.assertEqual(signed['affine_support_phase_pairs'],6528)
        self.assertEqual(signed['local_OR_signed_minimum'],2)
        self.assertEqual(signed['local_OR_positive_minimum'],3)

    def test_counts_guards_and_recurrences(self):
        for m in range(65):
            row=c.counts(m)
            self.assertLessEqual(row['positive_piece_lower'],row['partition_piece_upper'])
            self.assertEqual(row['positive_piece_lower'],(7**m+4**m-1)//4**m)
            self.assertEqual(Fraction(*row['squared_normalized_overlap']),Fraction(7,8)**m)
        for bad in [-1,True,1.0,513]:
            with self.assertRaises(ValueError):c.counts(bad)
        for bad in [-1,True,7]:
            with self.assertRaises(ValueError):list(c.affine_supports(bad))
        with self.assertRaises(ValueError):c.positive_partition(5)
        with self.assertRaises(ValueError):c.signed_inclusion(5)


if __name__=='__main__':unittest.main()
