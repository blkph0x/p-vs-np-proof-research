import unittest

from engine import (discover, parity_bits, records, reorder_gadget_blocks,
                    rename_variables, verify_record, xor_chain)
from gaussian_baseline import recover_xor_relation


class RepresentationDiscoveryTests(unittest.TestCase):
    def test_chain_projects_to_even_parity(self):
        for count in range(3, 8):
            chain = xor_chain(count)
            result = discover(chain)
            self.assertEqual(result.projected_bits, parity_bits(count))
            self.assertEqual(result.local_count, count - 1)

    def test_semantics_survive_variable_renaming(self):
        for count in range(3, 8):
            identity = discover(xor_chain(count))
            reversed_names = discover(xor_chain(count, tuple(reversed(range(count)))))
            self.assertEqual(identity.projected_bits, reversed_names.projected_bits)
            self.assertEqual(identity.encoded_representation_bits,
                             reversed_names.encoded_representation_bits)
            self.assertEqual(identity.enumeration_discovery_work,
                             reversed_names.enumeration_discovery_work)

    def test_discovery_work_grows_while_representation_stays_linear(self):
        rows = [discover(xor_chain(count)) for count in range(3, 8)]
        self.assertTrue(all(row.encoded_representation_bits > 0 for row in rows))
        self.assertEqual(len({row.encoded_representation_bits for row in rows}), 5)
        self.assertTrue(all(left.enumeration_discovery_work < right.enumeration_discovery_work
                            for left, right in zip(rows, rows[1:])))
        self.assertTrue(all(row.enumeration_discovery_work >= row.exhaustive_replay_work for row in rows))

    def test_saved_record_replays_exactly(self):
        chain = xor_chain(5, (2, 4, 0, 3, 1))
        record = discover(chain)
        self.assertTrue(verify_record(chain, record))

    def test_invalid_permutation_is_rejected(self):
        with self.assertRaises(ValueError):
            xor_chain(4, (0, 1, 1, 3))

    def test_gaussian_baseline_recovers_the_hidden_relation(self):
        for count in range(3, 8):
            chain = xor_chain(count, tuple(reversed(range(count))))
            result = recover_xor_relation(tuple(chain["clauses"]), tuple(chain["shared"]))
            self.assertEqual(result.status, "EXACT_AFFINE")
            self.assertEqual(result.support, tuple(range(count)))
            self.assertEqual(result.rhs, 0)

    def test_gaussian_baseline_survives_syntactic_controls(self):
        chain = xor_chain(5)
        renamed = rename_variables(chain, {index: 8 - index for index in range(9)})
        for variant in (
            reorder_gadget_blocks(chain),
            reorder_gadget_blocks(chain, duplicate_block=0),
            renamed,
        ):
            result = recover_xor_relation(tuple(variant["clauses"]), tuple(variant["shared"]))
            self.assertEqual((result.status, result.support, result.rhs),
                             ("EXACT_AFFINE", tuple(range(5)), 0))

    def test_gaussian_baseline_fails_closed_on_mutated_gadget(self):
        chain = xor_chain(4)
        clauses = list(chain["clauses"])
        clauses[0] = (clauses[0][0], clauses[0][1], -clauses[0][2])
        result = recover_xor_relation(tuple(clauses), tuple(chain["shared"]))
        self.assertNotEqual(result.status, "EXACT_AFFINE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
