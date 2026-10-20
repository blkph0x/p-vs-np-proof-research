import unittest

from nonlinear_control import classify, is_affine_relation, projected_relation


class NonlinearControlTests(unittest.TestCase):
    def test_control_is_not_affine(self):
        self.assertFalse(is_affine_relation(projected_relation(), 3))
        self.assertEqual(classify()["status"], "NOT_AFFINE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
