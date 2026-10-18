"""Reproduce the independent original-count audit; never edits production.

This script writes only INDEPENDENT_REVIEW.json in its own directory. Its
small truth enumeration and larger original-assignment search do not call
producer restriction, component, or counting helpers as reference oracles.
"""
import copy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import random

import reference as ref

HERE = Path(__file__).resolve().parent


def original_assignment_search(n, clauses, max_calls=1000000, max_models=100000):
    """Complete original-variable DFS, with direct unit propagation only."""
    rows = []
    for clause in clauses:
        positive = sum(1 << (v-1) for v in set(clause) if v > 0)
        negative = sum(1 << (-v-1) for v in set(clause) if v < 0)
        if not positive & negative:
            rows.append((positive, negative))
    calls = 0
    models = set()

    def recurse(assigned, ones):
        nonlocal calls
        calls += 1
        if calls > max_calls:
            raise RuntimeError('independent audit call budget exceeded')
        while True:
            unresolved = 0
            forced = None
            for positive, negative in rows:
                if positive & ones or negative & (assigned ^ ones):
                    continue
                remaining = (positive | negative) & ~assigned
                if not remaining:
                    return 0
                unresolved |= remaining
                if remaining.bit_count() == 1:
                    forced = remaining, bool(positive & remaining)
                    break
            if forced is None:
                break
            bit, value = forced
            assigned |= bit
            if value:
                ones |= bit
        if not unresolved:
            free = [i for i in range(n) if not assigned >> i & 1]
            if len(free) >= max_models.bit_length() or len(models) + (1 << len(free)) > max_models:
                raise RuntimeError('independent audit model budget exceeded')
            for choice in range(1 << len(free)):
                word = ones
                for j, variable in enumerate(free):
                    word |= ((choice >> j) & 1) << variable
                assert all(any(bool(word >> (abs(lit)-1) & 1) == (lit > 0)
                               for lit in clause) for clause in clauses)
                assert word not in models
                models.add(word)
            return 1 << len(free)
        bit = unresolved & -unresolved
        return recurse(assigned | bit, ones) + recurse(assigned | bit, ones | bit)

    count = recurse(0, 0)
    assert count == len(models)
    return dict(count=count, search_calls=calls, models=sorted(models),
                max_calls=max_calls, max_models=max_models,
                method='original-assignment DFS, direct units, no memoization or components')


def backward_sliding_count(n, clauses):
    assert n == len(clauses) + 2
    assert all(sorted(abs(lit) for lit in clause) == [i+1, i+2, i+3]
               for i, clause in enumerate(clauses))

    @lru_cache(None)
    def suffix(i, a, b):
        if i == len(clauses):
            return 1
        total = 0
        for c in (0, 1):
            values = {i+1: a, i+2: b, i+3: c}
            if any(bool(values[abs(lit)]) == (lit > 0) for lit in clauses[i]):
                total += suffix(i+1, b, c)
        return total

    count = sum(suffix(0, a, b) for a in (0, 1) for b in (0, 1))
    return dict(count=count, memoized_suffix_states=suffix.cache_info().currsize,
                method='independent backward original-clause suffix recurrence')


def run():
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    sources = list(saved['source_sha256']) + ['RESULTS.json', 'independent_review.py', 'INDEPENDENT_REVIEW.md']
    before = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in sources}
    for name, digest in saved['source_sha256'].items():
        assert before[name] == digest, name
    for case in saved['cases']:
        assert ref.verify(case['n'], case['clauses'], case['result'], **case['caps'])['valid'], case['name']
        assert case['result']['count'] == case['independent_control_count']

    rng = random.Random(2026101902)
    messages = mutations = assignments = original_words = 0
    positive_coverage_controls = 0
    def truth(n, clauses):
        nonlocal assignments
        answer = 0
        for word in range(1 << n):
            assignments += 1
            answer += all(any(bool(word >> (abs(lit)-1) & 1) == (lit > 0)
                              for lit in clause) for clause in clauses)
        return answer

    def local_count(formula):
        variables = sorted({abs(lit) for clause in formula for lit in clause})
        mapping = {v: i+1 for i, v in enumerate(variables)}
        renamed = [[mapping[abs(lit)] * (1 if lit > 0 else -1) for lit in clause]
                   for clause in formula]
        return truth(len(variables), renamed)

    for _ in range(400):
        n = rng.randrange(9)
        clauses = [[rng.choice((-1, 1)) * rng.randrange(1, n+1)
                    for _ in range(rng.randrange(5))]
                   for _ in range(rng.randrange(11))] if n else ([[]] if rng.randrange(2) else [])
        result = ref.solve(n, clauses)
        assert result['status'] == 'EXACT' and ref.verify(n, clauses, result)['valid']
        expected = truth(n, clauses)
        original_words += 1 << n
        assert result['count'] == expected
        for i, node in enumerate(result['certificate']['nodes']):
            assert local_count(node['formula']) == node['count']
            messages += 1
            changed = copy.deepcopy(result)
            changed['certificate']['nodes'][i]['count'] += 1
            assert not ref.verify(n, clauses, changed)['valid']
            mutations += 1
        if expected:
            changed = copy.deepcopy(result)
            external = clauses + [[]]
            changed['certificate']['input_sha256'] = ref.request_hash(n, external)
            assert not ref.verify(n, external, changed)['valid']
            positive_coverage_controls += 1

    larger = []
    for case in saved['cases']:
        if 'planted_mixed' in case['name']:
            audit = original_assignment_search(case['n'], case['clauses'])
        elif case['name'] == 'legacy_sliding_64_radius2_seed17':
            audit = backward_sliding_count(case['n'], case['clauses'])
        else:
            continue
        assert audit['count'] == case['result']['count']
        larger.append(dict(name=case['name'], n=case['n'], clauses=case['clauses'],
                           original_input_sha256=case['input_sha256'], **audit))
    after = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in sources}
    assert before == after
    summary = dict(saved_original_exact_replayed=len(saved['cases']),
                   saved_source_references_checked=len(saved['source_sha256']),
                   additional_formulas=400, direct_original_assignments=original_words,
                   direct_original_and_residual_assignments=assignments,
                   residual_counts_checked=messages, count_mutations_rejected=mutations,
                   forged_hash_added_empty_clause_rejections=positive_coverage_controls,
                   complete_original_models=sum(len(case.get('models', [])) for case in larger))
    assert messages == mutations == 735 and summary['complete_original_models'] == 744
    output = dict(format='independent-original-count-review-v1', seed=2026101902,
                  source_sha256=before, source_unchanged_during_run=True,
                  summary=summary, larger_originals=larger)
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    run()
