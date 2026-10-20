import unittest

from engine import discover, parity_bits, records, verify_record, xor_chain


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
            self.assertEqual(identity.representation_bits, reversed_names.representation_bits)
            self.assertEqual(identity.discovery_work, reversed_names.discovery_work)

    def test_discovery_work_grows_while_representation_stays_linear(self):
        rows = [discover(xor_chain(count)) for count in range(3, 8)]
        self.assertTrue(all(row.representation_bits > 0 for row in rows))
        self.assertEqual(len({row.representation_bits for row in rows}), 5)
        self.assertTrue(all(left.discovery_work < right.discovery_work
                            for left, right in zip(rows, rows[1:])))
        self.assertTrue(all(row.discovery_work >= row.verification_work for row in rows))

    def test_saved_record_replays_exactly(self):
        chain = xor_chain(5, (2, 4, 0, 3, 1))
        record = discover(chain)
        self.assertTrue(verify_record(chain, record))

    def test_invalid_permutation_is_rejected(self):
        with self.assertRaises(ValueError):
            xor_chain(4, (0, 1, 1, 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
