import copy
import importlib.util
import itertools
from pathlib import Path
import random
import sys
import unittest

import planner


def xor3(support, rhs):
    return [[-(v+1) if (word >> j) & 1 else v+1 for j, v in enumerate(support)]
            for word in range(8) if word.bit_count() % 2 != rhs]


def count(n, clauses):
    return sum(all(any(bool(word & (1 << (abs(lit)-1))) == (lit > 0) for lit in clause)
                   for clause in clauses) for word in range(1 << n))


def solver():
    path = Path(__file__).resolve().parent.parent/'compressed_affine_dag_lab'/'dag.py'
    spec = importlib.util.spec_from_file_location('grouping_test_frozen_solver', path)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestPlanner(unittest.TestCase):
    def verified(self, n, clauses, **caps):
        result = planner.plan(n, clauses, **caps)
        self.assertEqual(result['status'], 'EXACT')
        checked = planner.verify_plan(n, clauses, result, **caps)
        self.assertTrue(checked['valid'], checked)
        self.assertEqual(sorted(checked['order']), list(range(len(clauses))))
        return result

    def test_every_complete_xor3_support_and_polarity(self):
        for support in itertools.combinations(range(6), 3):
            for rhs in (0, 1):
                clauses = xor3(support, rhs)
                result = self.verified(6, clauses)
                self.assertEqual(len(result['certificate']['groups']), 1)
                self.assertEqual(result['certificate']['groups'][0]['rhs'], rhs)
                self.assertEqual(count(6, clauses), 32)

    def test_shuffled_occurrences_have_canonical_complete_blocks(self):
        clauses = xor3([0, 1, 2], 0)+xor3([1, 3, 4], 1)+xor3([0, 2, 5], 1)
        target = self.verified(6, clauses)
        ordered = [clauses[i] for i in target['order']]
        rng = random.Random(2026101861)
        for _ in range(40):
            shuffled = list(clauses); rng.shuffle(shuffled)
            result = self.verified(6, shuffled)
            self.assertEqual([shuffled[i] for i in result['order']], ordered)
            self.assertEqual(count(6, shuffled), count(6, ordered))

    def test_ungrouped_and_duplicate_occurrences_are_retained(self):
        block = xor3([0, 1, 2], 1)
        for clauses in [block+[block[0]], block+block, block+xor3([0, 1, 2], 0)]:
            result = self.verified(4, clauses)
            self.assertEqual(result['certificate']['groups'], [])
            self.assertEqual(result['order'], list(range(len(clauses))))
        clauses = [[1, -1, 2], [], [4, 4], [1, 2]]+block
        result = self.verified(4, clauses)
        self.assertEqual(result['certificate']['ungrouped_ids'], [0, 1, 2, 3])
        self.assertEqual(result['order'][-4:], [0, 1, 2, 3])

    def test_incomplete_mixed_parity_and_repeated_variables_not_blocks(self):
        for clauses in [xor3([0, 1, 2], 0)[:-1],
                        xor3([0, 1, 2], 0)[:-1]+xor3([0, 1, 2], 1)[:1],
                        [[1, 1, 2], [-1, 1, 2], [1, -1, -2], [-1, -1, -2]]]:
            result = self.verified(3, clauses)
            self.assertFalse(result['certificate']['groups'])

    def test_strict_original_types_and_literal_bounds(self):
        for n, clauses in [(True, []), (1, [[True]]), (1, [[False]]), (1, [[0]]),
                           (1, [[2]]), (1, [[1.0]])]:
            with self.assertRaises(ValueError): planner.plan(n, clauses)

    def test_source_rebinding_and_complete_partition(self):
        clauses = xor3([0, 1, 2], 0)+[[4]]
        original = self.verified(4, clauses)
        self.assertFalse(planner.verify_plan(4, clauses+[[]], original)['valid'])
        self.assertFalse(planner.verify_plan(5, clauses, original)['valid'])
        changed = copy.deepcopy(original)
        binding = planner.input_hash(4, clauses+[[]])
        changed['input_sha256'] = changed['certificate']['input_sha256'] = binding
        self.assertFalse(planner.verify_plan(4, clauses+[[]], changed)['valid'])

    def test_occurrence_metadata_mutations(self):
        clauses = xor3([0, 1, 2], 1)+[[4]]
        original = self.verified(4, clauses)
        mutations = [lambda r: r['certificate']['groups'][0]['occurrence_ids'].__setitem__(0, False),
                     lambda r: r['certificate']['groups'][0]['occurrence_ids'].__setitem__(0, 1),
                     lambda r: r['certificate']['groups'][0]['occurrence_ids'].__setitem__(0, -1),
                     lambda r: r['certificate']['groups'][0]['support'].__setitem__(0, True),
                     lambda r: r['certificate']['groups'][0].__setitem__('rhs', True),
                     lambda r: r['certificate']['groups'][0].__setitem__('forbidden_parity', 1),
                     lambda r: r['certificate']['ungrouped_ids'].clear(),
                     lambda r: r['order'].pop(),
                     lambda r: r['certificate']['order'].reverse()]
        for mutate in mutations:
            changed = copy.deepcopy(original); mutate(changed)
            self.assertFalse(planner.verify_plan(4, clauses, changed)['valid'])

    def test_fake_subset_block_on_duplicate_bucket_rejected(self):
        clauses = xor3([0, 1, 2], 0)
        old = self.verified(3, clauses)
        changed = copy.deepcopy(old)
        duplicate = clauses+[clauses[0]]
        binding = planner.input_hash(3, duplicate)
        changed['input_sha256'] = changed['certificate']['input_sha256'] = binding
        changed['certificate']['ungrouped_ids'] = [4]
        changed['certificate']['order'].append(4)
        self.assertFalse(planner.verify_plan(3, duplicate, changed)['valid'])

    def test_caps_unknown_without_partial_proposal(self):
        clauses = xor3([0, 1, 2], 0)
        exact = self.verified(3, clauses)
        for caps in [{'max_variables': 2}, {'max_clauses': 3}, {'max_literals': 11},
                     {'max_blocks': 0}, {'max_work': 0}]:
            result = planner.plan(3, clauses, **caps)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIsNone(result['order']); self.assertIsNone(result['certificate'])
            self.assertEqual(planner.verify_plan(3, clauses, exact, **caps)['status'], 'UNKNOWN')

    def test_empty_formula_and_no_blocks_are_identity_orders(self):
        for n, clauses in [(0, []), (5, []), (2, [[1], [-2], [1, -1]])]:
            result = self.verified(n, clauses)
            self.assertEqual(result['order'], list(range(len(clauses))))

    def test_actual_frozen_solver_order_invariance(self):
        engine = solver()
        rng = random.Random(2026101862)
        for _ in range(50):
            n = rng.randrange(3, 7)
            support = sorted(rng.sample(range(n), 3))
            clauses = xor3(support, rng.randrange(2))
            clauses += [[rng.choice((-1, 1))*rng.randrange(1, n+1)
                         for __ in range(rng.randrange(4))] for ___ in range(rng.randrange(5))]
            rng.shuffle(clauses)
            proposal = self.verified(n, clauses)
            result = engine.solve_formula(n, clauses, order=proposal['order'])
            self.assertEqual(result['status'], 'EXACT')
            self.assertEqual(result['count'], count(n, clauses))
            self.assertTrue(engine.verify_formula(n, clauses, result, order=proposal['order'])['valid'])


if __name__ == '__main__':
    unittest.main()
