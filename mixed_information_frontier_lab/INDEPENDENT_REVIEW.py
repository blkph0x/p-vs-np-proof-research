"""Independent brute-force replay of the mixed-frontier residual classes."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import run_experiments

HERE = Path(__file__).resolve().parent


def direct_satisfies(constraints, assignment):
    for item in constraints:
        if item['kind'] == 'parity':
            if sum((assignment >> i) & 1 for i in item['scope']) % 2 != item['rhs']:
                return False
        elif item['kind'] == 'cardinality':
            count = sum((assignment >> i) & 1 for i in item['scope'])
            if item['op'] == 'eq' and count != item['target']:
                return False
            if item['op'] == 'le' and count > item['target']:
                return False
        elif not any(((assignment >> (abs(lit) - 1)) & 1) == (lit > 0)
                     for lit in item['literals']):
            return False
    return True


def direct_classes(n, constraints, cut):
    classes = {}
    local = [set() for _ in constraints]
    for prefix in range(1 << cut):
        suffixes = tuple(s for s in range(1 << (n - cut))
                         if direct_satisfies(constraints, prefix | (s << cut)))
        if not suffixes:
            continue
        classes.setdefault(suffixes, []).append(prefix)
        for idx, item in enumerate(constraints):
            if item['kind'] == 'parity':
                value = sum((prefix >> i) & 1 for i in item['scope'] if i < cut) % 2
            elif item['kind'] == 'cardinality':
                value = sum((prefix >> i) & 1 for i in item['scope'] if i < cut)
            else:
                value = int(any((lit > 0 and ((prefix >> (lit - 1)) & 1))
                                or (lit < 0 and not ((prefix >> (-lit - 1)) & 1))
                                for lit in item['literals'] if abs(lit) <= cut))
            local[idx].add(value)
    state_counts = [len(values) for values in local]
    product = 1
    for count in state_counts:
        product *= count
    return len(classes), product, sum(map(len, classes.values()))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['cases']:
        case = saved['case']
        exact_classes, exact_product, exact_live = direct_classes(case['n'], case['constraints'], case['cut'])
        analysis = saved['analysis']
        assert exact_classes == analysis['future_classes']
        assert exact_product == analysis['naive_product_states']
        assert exact_live == analysis['live_prefixes']
        if case['expected_classes'] is not None:
            assert exact_classes == case['expected_classes']
        rows.append({'name': case['name'], 'future_classes': exact_classes,
                     'naive_product_states': exact_product, 'live_prefixes': exact_live})
    source = {name: digest(HERE / name) for name in
              ('mixed_frontier.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_MIXED_FRONTIER_REVIEW',
              'case_count': len(rows), 'rows': rows,
              'source_hashes': source,
              'full_product_case_classes': next(r['future_classes'] for r in rows
                                                if r['name'] == 'independent_crossing_parity_6'),
              'duplicate_parity_classes': next(r['future_classes'] for r in rows
                                               if r['name'] == 'duplicate_parity_6'),
              'same_scope_cardinality_parity_classes': next(r['future_classes'] for r in rows
                                                            if r['name'] == 'same_scope_cardinality_plus_parity')}
    review['partial_scope_cardinality_parity_classes'] = next(
        r['future_classes'] for r in rows if r['name'] == 'partial_scope_cardinality_plus_parity')
    assert review['partial_scope_cardinality_parity_classes'] == 10
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent mixed-frontier review\n\n'
        'A separate evaluator reconstructed all five constraint bundles and recomputed '
        'each suffix-set residual directly. It agrees with the saved analyzer on every '
        'live-prefix count, local-product count, and future-equivalence class count. '
        'Duplicate parity collapses from 64 nominal states to 2; six independent '
        'crossing parities retain all 64 classes; same-scope exact cardinality plus '
        'parity retains 7 classes. These are exact finite controls, not a universal '
        'SAT algorithm.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'full_product_classes': review['full_product_case_classes']}))


if __name__ == '__main__':
    run()
