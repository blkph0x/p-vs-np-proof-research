"""Save bounded original requests, complete marginal proofs and exact controls."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import random
from time import perf_counter

import boundary as b
from test_boundary import enumerate_marginal, evaluate, pair_family

HERE = Path(__file__).resolve().parent
SOURCES = ['boundary.py', 'test_boundary.py', 'run_experiments.py', 'THEOREM.md']


def run():
    before = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}
    cases = []
    assignment_words = 0
    def record(name, request, caps=None, reference=None):
        nonlocal assignment_words
        caps = caps or {}
        request = dict(request)
        request['scalar'] = b.pack(b.ratio(request.get('scalar', 1)))
        started = perf_counter()
        result = b.marginalize(**request, **caps)
        solve_seconds = perf_counter() - started
        verification = None
        if result['status'] == 'EXACT':
            started = perf_counter()
            verification = b.verify_marginal(**request, result=result, **caps)
            verify_seconds = perf_counter() - started
            assert verification['valid'], verification
        else:
            verify_seconds = None
        if reference is None and request['n'] <= 8:
            original = {key: value for key, value in request.items() if key != 'order'}
            table = enumerate_marginal(**original)
            assignment_words += 1 << len(request.get('active', list(range(request['n']))))
            if result['status'] == 'EXACT':
                for bits, value in table.items():
                    word = sum(bit << i for i, bit in zip(request['retained'], bits))
                    assert evaluate(result['message'], word) == value
            reference = {'kind': 'bounded_original_assignment_enumeration',
                         'values': [{'bits': list(bits), 'value': b.pack(value)} for bits, value in table.items()]}
        cases.append(dict(name=name, request=request, caps=caps, reference=reference,
                          result=result, verification=verification,
                          solve_seconds=solve_seconds, verify_seconds=verify_seconds))
        return result

    record('one_internal_pin', dict(n=2, retained=[0], equations=[], phase=[3], scalar=1))
    record('forced_substitution', dict(n=4, retained=[0, 1, 2], equations=[(11, 0)], phase=[12], scalar=1))
    record('signed_zero', dict(n=1, retained=[], equations=[], phase=[1], scalar=1))
    record('empty_signed_scalar', dict(n=0, retained=[], equations=[], phase=[0], scalar=Fraction(3, 7)))
    record('inconsistent_original', dict(n=3, retained=[1], equations=[(1, 0), (1, 1)], phase=[6], scalar=1))
    record('zero_original_scalar', dict(n=5, retained=[4, 0], equations=[(3, 1)], phase=[17], scalar=0))
    record('dependent_support_and_constant_sign', dict(n=3, retained=[2, 0, 1], equations=[(3, 1), (6, 0), (5, 1)], phase=[1, 3], scalar=Fraction(-2, 5)))
    record('inactive_coordinates_not_summed', dict(n=8, retained=[7], active=[7], equations=[], phase=[], scalar=1))
    for k in (1, 8, 64, 256):
        result = record('signed_pair_product_' + str(k), pair_family(k),
                        reference={'kind': 'all_size_product_identity', 'factors': k, 'scalar': [1 << k, 1],
                                   'phase': [(1 << (2*i)) | (1 << (2*i+1)) for i in range(k)]})
        assert result['message']['scalar'] == [1 << k, 1]
        assert result['message']['equations'] == []
        assert result['message']['phase'] == cases[-1]['reference']['phase']
    for k in (1, 32, 256):
        request = dict(n=2*k, retained=list(range(k)), equations=[], phase=[(1 << i) | (1 << (k+i)) for i in range(k)], scalar=1)
        result = record('pin_product_' + str(k), request,
                        reference={'kind': 'all_size_product_identity', 'factors': k, 'scalar': [1 << k, 1], 'pins': list(range(k))})
        assert result['message']['scalar'] == [1 << k, 1]
        assert result['message']['equations'] == [[1 << i, 0] for i in range(k)]
    result = record('512_unused_active_bits', dict(n=512, retained=[], equations=[], phase=[], scalar=1),
                    reference={'kind': 'unused_active_bit_product', 'value': [1 << 512, 1]})
    assert result['message']['scalar'] == [1 << 512, 1]
    rng = random.Random(2026101901)
    for case in range(80):
        n = rng.randrange(8)
        active = [i for i in range(n) if rng.randrange(4)]
        retained = [i for i in active if rng.randrange(2)]
        rng.shuffle(retained)
        order = [i for i in active if i not in retained]
        rng.shuffle(order)
        equations = [(sum(1 << i for i in active if rng.randrange(2)), rng.randrange(2)) for _ in range(rng.randrange(7))]
        terms = [0] + [1 << i for i in active] + [(1 << i) | (1 << j) for i in active for j in active if i < j]
        phase = [term for term in terms if rng.randrange(2)]
        record('seeded_original_' + str(case), dict(n=n, retained=retained, active=active, order=order,
               equations=equations, phase=phase, scalar=Fraction(rng.randrange(-3, 4), rng.randrange(1, 5))))
    for name, caps in [('work', {'max_work': 0}), ('rows', {'max_rows': 0}),
                       ('phase', {'max_terms': 5}), ('steps', {'max_steps': 3}),
                       ('scalar', {'max_scalar_bits': 2})]:
        result = record('interrupted_' + name, pair_family(2), caps)
        assert result['status'] == 'UNKNOWN'
    result = record('binary_encoded_huge_dimension', dict(n=10**12, retained=[], equations=[], phase=[], scalar=1),
                    reference={'kind': 'dimension_guard_before_allocation'})
    assert result['status'] == 'UNKNOWN'
    after = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}
    assert before == after
    output = dict(format='compact-affine-boundary-experiments-v1', source_sha256=after,
                  source_unchanged_during_run=True,
                  summary=dict(cases=len(cases), statuses=dict(Counter(c['result']['status'] for c in cases)),
                               bounded_original_assignment_words=assignment_words,
                               largest_signed_boundary=512, largest_signed_internal_count=512), cases=cases)
    (HERE/'RESULTS.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(output['summary'], sort_keys=True))


if __name__ == '__main__':
    run()
