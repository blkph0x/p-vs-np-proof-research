import unittest

from engine import (direct_count, paired_or_blocks, solve, solve_components,
                    verify, verify_components)


class CharacterFactorTests(unittest.TestCase):
    def check_exact(self, n, blocks, rows, rhs, expected):
        result = solve(n, blocks, rows, rhs)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["value"], [expected, 1])
        checked = verify(n, blocks, rows, rhs, result)
        self.assertEqual(checked["status"], "VERIFIED", checked)
        self.assertTrue(checked["valid"])
        if n <= 12:
            self.assertEqual(direct_count(n, blocks, rows, rhs), expected)
        return result

    def test_global_even_or_formula(self):
        for m in range(1, 8):
            n, blocks, rows, rhs = paired_or_blocks(m, "global")
            expected = (3 ** m + (-1) ** m) // 2
            result = self.check_exact(n, blocks, rows, rhs, expected)
            self.assertEqual(result["rank"], 1)
            self.assertEqual(result["stats"]["characters"], 2)

    def test_no_affine_constraint_is_product(self):
        for m in range(0, 8):
            n, blocks, rows, rhs = paired_or_blocks(m, "none")
            self.check_exact(n, blocks, rows, rhs, 3 ** m)

    def test_local_parities_are_a_rank_barrier(self):
        for m in range(1, 7):
            n, blocks, rows, rhs = paired_or_blocks(m, "local")
            # Each pair must be 11, so there is one accepted assignment.
            result = self.check_exact(n, blocks, rows, rhs, 1)
            self.assertEqual(result["rank"], m)
            self.assertEqual(result["stats"]["characters"], 1 << m)

    def test_inconsistent_affine_system(self):
        n, blocks, _, _ = paired_or_blocks(2, "none")
        result = solve(n, blocks, [0, 0], [0, 1])
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["value"], [0, 1])
        self.assertTrue(verify(n, blocks, [0, 0], [0, 1], result)["valid"])

    def test_character_cap_is_unknown(self):
        n, blocks, rows, rhs = paired_or_blocks(8, "local")
        result = solve(n, blocks, rows, rhs, {"max_characters": 64})
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn("value", result)

    def test_mutated_certificate_rejected(self):
        n, blocks, rows, rhs = paired_or_blocks(3, "global")
        result = solve(n, blocks, rows, rhs)
        result["characters"][0]["local"][0]["value"] += 1
        checked = verify(n, blocks, rows, rhs, result)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")

    def test_source_mutation_rejected(self):
        n, blocks, rows, rhs = paired_or_blocks(3, "global")
        result = solve(n, blocks, rows, rhs)
        changed = [dict(block) for block in blocks]
        changed[0] = {**changed[0], "factors": [dict(changed[0]["factors"][0])]} 
        changed[0]["factors"][0]["table"] = [0, 1, 1, 0]
        checked = verify(n, changed, rows, rhs, result)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")

    def test_overlapping_character_rows_xor_on_a_block(self):
        blocks = [
            {"id": "b0", "scope": [0], "factors":
             [{"id": "f0", "scope": [0], "table": [-2, -1]}]},
            {"id": "b1", "scope": [1], "factors":
             [{"id": "f1", "scope": [1], "table": [1, 0]}]},
            {"id": "b2", "scope": [2], "factors":
             [{"id": "f2", "scope": [2], "table": [-2, 1]}]},
        ]
        rows, rhs = [5, 3], [1, 0]
        expected = direct_count(3, blocks, rows, rhs)
        result = self.check_exact(3, blocks, rows, rhs, expected)
        self.assertEqual(result["value"], [expected, 1])

    def test_component_factorization_splits_local_parities(self):
        n, blocks, rows, rhs = paired_or_blocks(10, "local")
        result = solve_components(n, blocks, rows, rhs)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["value"], [1, 1])
        self.assertEqual(result["component_count"], 10)
        self.assertEqual(result["stats"]["component_characters"], [2] * 10)
        checked = verify_components(n, blocks, rows, rhs, result)
        self.assertTrue(checked["valid"], checked)

    def test_component_factorization_cannot_split_connected_rank(self):
        n, blocks, rows, rhs = paired_or_blocks(8, "connected")
        result = solve_components(n, blocks, rows, rhs)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["value"], [1, 1])
        self.assertEqual(result["component_count"], 1)
        self.assertEqual(result["stats"]["component_characters"], [256])
        self.assertTrue(verify_components(n, blocks, rows, rhs, result)["valid"])

    def test_component_mutation_rejected(self):
        n, blocks, rows, rhs = paired_or_blocks(4, "local")
        result = solve_components(n, blocks, rows, rhs)
        result["components"][0]["block_indices"] = [1]
        checked = verify_components(n, blocks, rows, rhs, result)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")

    def test_connected_component_cap_is_unknown(self):
        n, blocks, rows, rhs = paired_or_blocks(16, "connected")
        result = solve_components(n, blocks, rows, rhs, {"max_work": 100_000})
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn("value", result)


if __name__ == "__main__":
    unittest.main()
