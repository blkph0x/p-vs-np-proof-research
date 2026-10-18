"""Read-only original-control checks; writes only its own review artifact."""
import copy
from hashlib import sha256
import itertools
import json
from pathlib import Path
import time
from controls import fixed_controls, verify_control

HERE = Path(__file__).resolve().parent
SOURCES = ['controls.py', 'test_controls.py', 'THEOREM.md',
           'independent_review.py', 'INDEPENDENT_REVIEW.md']


def hashes():
    return {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def original_truth_count(case):
    return sum(all(any(bool(word >> (abs(literal)-1) & 1) == (literal > 0) for literal in clause)
                   for clause in case['clauses']) for word in range(1 << case['n']))


def main():
    before = hashes(); started = time.perf_counter()
    cases = fixed_controls(); mutations = 0; control_records = []
    for case in cases:
        checked = verify_control(case)
        for index in range(len(case['clauses'])):
            bad = copy.deepcopy(case); del bad['clauses'][index]
            try:
                verify_control(bad)
            except AssertionError:
                mutations += 1
            else:
                raise AssertionError('accepted a missing original clause occurrence')
        record = dict(name=case['name'], n=case['n'], clauses=len(case['clauses']),
                      structural_count=checked['count'], single_clause_omissions_rejected=len(case['clauses']))
        if case['kind'] == 'pigeonhole':
            p, h = case['pigeons'], case['holes']
            # Independent feasible-column enumeration: each hole is empty or
            # assigned exactly one pigeon. Then test every row's nonemptiness.
            choices = itertools.product(range(-1, p), repeat=h)
            count = sum(set(range(p)).issubset(choice) for choice in choices)
            assert count == checked['count']
            record['independent_column_assignment_count'] = count
            record['independent_column_assignments_examined'] = (p+1)**h
        control_records.append(record)
    pairs = []
    for a, b in zip(cases[:16:2], cases[1:16:2]):
        assert a['edges'] == b['edges'] and a['charges'] == b['charges']
        assert sorted(map(tuple, a['clauses'])) == sorted(map(tuple, b['clauses']))
        assert a['expected_count'] == b['expected_count']
        pairs.append([a['name'], b['name']])
    from controls import parity_control, pigeonhole_control
    small = [parity_control(v, charge, 20261018+v, shuffled)
             for v in (4, 6, 8) for charge in (0, 1) for shuffled in (False, True)]
    small += [pigeonhole_control(p, h) for h in (1, 2, 3) for p in (h, h+1)]
    truth_words = 0
    for case in small:
        assert original_truth_count(case) == verify_control(case)['count']
        truth_words += 1 << case['n']
    after = hashes(); assert before == after
    result = dict(verdict='CLEAN: complete original-clause controls and scoped structural counts',
                  source_sha256=before, source_unchanged_during_run=True,
                  source_controls=len(cases), single_clause_omissions_rejected=mutations,
                  grouped_shuffled_pairs=pairs, independent_pigeonhole_column_counts=6,
                  small_original_formulas=len(small), small_original_truth_words=truth_words,
                  seconds=time.perf_counter()-started, controls=control_records,
                  scope='This audits source construction/counts, not solver performance; grouped/shuffled solver outcomes must remain separate.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('source_controls', 'single_clause_omissions_rejected',
                     'independent_pigeonhole_column_counts', 'small_original_formulas', 'small_original_truth_words',
                     'source_unchanged_during_run')}))


if __name__ == '__main__':
    main()
