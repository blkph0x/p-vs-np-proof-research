import unittest

from projective_family import closed_form, verify_family


class ProjectiveFamilyTests(unittest.TestCase):
    def test_closed_form_rank_six(self):
        self.assertEqual(closed_form(6)['objective'], [42, 72, 192])
        self.assertEqual(closed_form(6)['stats'], [42, 6, 72, 192])
        self.assertEqual(closed_form(6)['native_state_count'], 64)

    def test_nontrivial_transforms(self):
        for r in (4, 5, 6, 8):
            transform = tuple((1 << i) | ((1 << (i + 1)) if i + 1 < r else 0)
                              for i in range(r))
            self.assertEqual(verify_family(r, transform), closed_form(r))

    def test_rank_twelve_control(self):
        self.assertEqual(verify_family(12)['columns'], 4095)
        self.assertEqual(verify_family(12)['native_state_count'], 4096)


if __name__ == '__main__':
    unittest.main()
