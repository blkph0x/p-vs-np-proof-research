"""Tiny exhaustive oracles independently check polynomial circuit decomposition."""
from itertools import combinations, permutations, product
import random
import unittest

from structural_probe import (conditioned_components, decompose_columns,
                              probe_stored_codes, validate_partition)


def span(values):
    result = {0}
    for value in values:
        result |= {other ^ value for other in tuple(result)}
    return result


def circuit_oracle(columns):
    """Enumerate only tiny test circuits, with no rank/elimination implementation."""
    n = len(columns)
    circuits = []
    for size in range(1, n + 1):
        for indices in combinations(range(n), size):
            mask = sum(1 << j for j in indices)
            value = 0
            for j in indices:
                value ^= columns[j]
            if not value and not any(mask & earlier == earlier for earlier in circuits):
                circuits.append(mask)
    adjacency = [set() for _ in columns]
    for mask in circuits:
        members = [j for j in range(n) if mask >> j & 1]
        for j in members:
            adjacency[j].update(members)
    unseen = set(range(n))
    result = []
    while unseen:
        reached, queue = set(), [min(unseen)]
        while queue:
            j = queue.pop()
            if j not in reached:
                reached.add(j)
                queue.extend(adjacency[j] - reached)
        unseen -= reached
        result.append(sorted(reached))
    return result


class StructuralProbeTest(unittest.TestCase):
    def check_decomposition(self, columns, basis=None):
        result = decompose_columns(columns, basis)
        self.assertEqual(result['components'], circuit_oracle(columns))
        self.assertTrue(result['partition_certificate']['valid'])
        self.assertEqual(1 << result['rank'], len(span(columns)))
        for item in result['fundamental_circuits']:
            circuit = item['coordinates']
            self.assertIn(item['nonbasis_coordinate'], circuit)
            value = 0
            for j in circuit:
                value ^= columns[j]
            self.assertEqual(value, 0)
            for omitted in circuit:
                rest = [columns[j] for j in circuit if j != omitted]
                self.assertEqual(len(span(rest)), 1 << len(rest))
        rank, n = result['rank'], len(columns)
        work = result['work']
        self.assertLessEqual(work['basis_discovery_xors'], n * rank)
        self.assertLessEqual(work['basis_setup_xors'], rank * rank)
        self.assertLessEqual(work['circuit_reduction_xors'], (n - rank) * rank)
        self.assertEqual(work['fundamental_circuits'], n - rank)
        self.assertEqual(work['successful_unions'], n - len(result['components']))
        return result

    def test_every_two_bit_representation_through_five_columns(self):
        count = 0
        for n in range(6):
            for columns in product(range(4), repeat=n):
                self.check_decomposition(columns)
                count += 1
        self.assertEqual(count, 1365)

    def test_higher_rank_random_representations_against_all_tiny_circuits(self):
        rng = random.Random(20261018)
        for _ in range(100):
            columns = tuple(rng.randrange(16) for _ in range(rng.randrange(1, 9)))
            self.check_decomposition(columns)

    def test_every_order_of_every_basis_gives_the_same_components(self):
        columns = (1, 2, 3, 4, 5, 6, 7, 0)
        tested = 0
        for basis in combinations(range(len(columns)), 3):
            if len(span(columns[j] for j in basis)) != 8:
                continue
            for ordered in permutations(basis):
                result = self.check_decomposition(columns, ordered)
                self.assertEqual(result['basis_indices'], list(ordered))
                self.assertEqual(result['work']['basis_discovery_columns'], 0)
                tested += 1
        self.assertEqual(tested, 168)

    def test_loops_coloops_parallel_blocks_and_large_bit_positions(self):
        columns = (0, 1, 1, 2, 4, 8, 12, 0, 1 << 128)
        result = self.check_decomposition(columns)
        self.assertEqual(result['components'], [[0], [1, 2], [3], [4, 5, 6], [7], [8]])
        self.assertEqual(result['loops'], [0, 7])
        self.assertEqual(result['coloops'], [3, 8])
        self.assertEqual(decompose_columns(())['components'], [])
        self.assertEqual(decompose_columns((0, 0), [])['components'], [[0], [1]])

    def test_invariance_under_row_operations_and_coordinate_permutations(self):
        columns = (1, 2, 3, 4, 8, 12, 0)
        expected = decompose_columns(columns)['components']
        transformed = tuple(value ^ (8 if value & 1 else 0) for value in columns)
        self.assertEqual(decompose_columns(transformed)['components'], expected)
        permutation = (6, 4, 2, 0, 5, 1, 3)
        permuted = decompose_columns(tuple(columns[j] for j in permutation))
        restored = sorted([sorted(permutation[j] for j in block)
                           for block in permuted['components']], key=lambda block: block[0])
        self.assertEqual(restored, expected)

    def test_independent_rank_certificate_accepts_direct_sums_only(self):
        columns = (1, 2, 3, 4)
        valid = validate_partition(columns, [[0, 1, 2], [3]])
        self.assertTrue(valid['valid'])
        self.assertEqual(valid['component_ranks'], [2, 1])
        self.assertEqual(valid['rank_sum'], 3)
        # Rank additivity alone certifies coarsenings, not irreducibility.
        self.assertTrue(validate_partition(columns, [[0, 1, 2, 3]])['valid'])
        for parts in [[[0], [1, 2], [3]], [[0, 1, 2]], [[0, 1, 2], [2, 3]],
                      [[0, 1, 2, 3], []], [[0, 1, 2, 4]], [[True, 0, 2, 3]]]:
            self.assertFalse(validate_partition(columns, parts)['valid'])

    def test_conditioned_components_preserve_original_coordinates(self):
        result = conditioned_components((3, 12), 4, deleted=(0,))
        self.assertEqual(result['remaining_coordinates'], [1, 2, 3])
        self.assertEqual(result['components'], [[0], [1, 2]])
        self.assertEqual(result['original_components'], [[1], [2, 3]])
        self.assertEqual(result['original_coloops'], [1])
        self.assertTrue(set(result['original_basis_indices']) <= {1, 2, 3})
        self.assertEqual(conditioned_components((3, 12), 4, deleted=(3, 0, 2, 1))[
                         'original_components'], [])
        full = conditioned_components((1, 2, 4), 3, deleted=(1,))
        self.assertEqual(full['original_components'], [[0], [2]])
        self.assertEqual(full['original_loops'], [0, 2])
        zero = conditioned_components((), 3, deleted=(1,))
        self.assertEqual(zero['original_coloops'], [0, 2])

    def test_stored_fixture_probe_without_conditioning(self):
        result = probe_stored_codes(max_delete=0)
        self.assertEqual(result['cases'], 6)
        self.assertEqual([item['n'] for item in result['codes']], [18, 20, 22, 24, 26, 28])
        for item in result['codes']:
            self.assertEqual(item['levels'][0]['max_components'], 1)
            self.assertEqual(item['levels'][0]['split_cases'], 0)

    def test_invalid_columns_bases_deletions_and_probe_limits(self):
        for columns in [(-1,), (True,), (1.5,)]:
            with self.assertRaises(ValueError):
                decompose_columns(columns)
        for basis in [(0, 0), (0, 3), (0, -1), (True,), (), (0,), (0, 1, 2)]:
            with self.assertRaises(ValueError):
                decompose_columns((1, 2, 3), basis)
        for deleted in [(0, 0), (4,), (-1,), (True,)]:
            with self.assertRaises(ValueError):
                conditioned_components((3, 12), 4, deleted)
        for limit in [-1, 3, True, 1.0]:
            with self.assertRaises(ValueError):
                probe_stored_codes(limit)


if __name__ == '__main__':
    unittest.main()
