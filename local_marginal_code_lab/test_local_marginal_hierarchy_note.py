"""Exact finite controls for the local-marginal hierarchy note."""

from __future__ import annotations

import itertools
import unittest


def _codewords():
    return tuple(
        word for word in itertools.product((0, 1), repeat=4)
        if (word[0] ^ word[1] ^ word[2]) == 0
        and (word[0] ^ word[1] ^ word[3]) == 0
    )


class LocalMarginalHierarchyNoteTests(unittest.TestCase):
    def test_global_projection_contains_only_equal_pair_bits(self):
        projected = {(word[2], word[3]) for word in _codewords()}
        self.assertEqual(projected, {(0, 0), (1, 1)})

    def test_check_local_pair_has_no_whole_check_scope(self):
        checks = ((0, 1, 2), (0, 1, 3))
        queried = {2, 3}
        self.assertTrue(all(not set(check).issubset(queried) for check in checks))
        self.assertEqual(
            {(a, b) for a in (0, 1) for b in (0, 1)},
            {(0, 0), (0, 1), (1, 0), (1, 1)},
        )

    def test_full_scope_distribution_is_exactly_supported_on_code(self):
        self.assertEqual(len(_codewords()), 4)
        self.assertTrue(all((word[2] == word[3]) for word in _codewords()))


if __name__ == "__main__":
    unittest.main()
