from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import random

from reference import equivalent_messages, marginalize_reference, pair, verify_reference
from test_reference import brute, message_value, wide_pair_request

HERE = Path(__file__).resolve().parent
SOURCE_NAMES = ['reference.py', 'test_reference.py', 'THEOREM.md', 'run_experiments.py']


def source_hashes():
    return {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCE_NAMES}


def run():
    start_hashes = source_hashes()
    cases = []
    choices = 0
    def add(name, request, reference=None, caps=None):
        nonlocal choices
        caps = caps or {}
        result = marginalize_reference(**request, **caps)
        verification = None
        oracle = None
        if result['status'] == 'EXACT':
            verification = verify_reference(request['n'], request['retained'], request['equations'], request['phase'],
                                            request.get('scalar', 1), result, active=request.get('active'), **caps)
            assert verification['valid'], (name, verification)
            active = request.get('active', list(range(request['n'])))
            if len(active) <= 9:
                expected = brute(request['n'], request['retained'], request['equations'], request['phase'], request.get('scalar', 1), active)
                oracle = [{'boundary_word': y, 'value': pair(v)} for y, v in expected.items()]
                assert all(message_value(result['message'], y) == v for y, v in expected.items())
                choices += 1 << len(active)
            if reference is not None:
                assert equivalent_messages(request['n'], request['retained'], result['message'], reference)['equivalent']
        cases.append(dict(name=name, request=request, caps=caps, result=result,
                          verification=verification, reference_message=reference, explicit_oracle=oracle))

    add('empty_identity', dict(n=0, retained=[], equations=[], phase=[], scalar=1))
    add('constant_negative_phase', dict(n=0, retained=[], equations=[], phase=[0], scalar=[3, 7]))
    add('zero_scalar', dict(n=12, retained=[7, 3], equations=[], phase=[1], scalar=0))
    add('inconsistent_original_support', dict(n=3, retained=[2], equations=[[3, 0], [3, 1]], phase=[], scalar=1))
    add('signed_internal_cancellation', dict(n=2, retained=[1], equations=[], phase=[1], scalar=1))
    add('forced_internal_affine_substitution', dict(n=3, retained=[2, 1], equations=[[7, 1]], phase=[5], scalar=[-2, 3]))
    add('dependent_rows_and_repeated_phase_terms', dict(n=4, retained=[3, 1], equations=[[5, 1], [5, 1], [0, 0]], phase=[3, 3, 0, 12], scalar=[5, 11]))
    add('inactive_coordinates_do_not_count', dict(n=1500, retained=[1400, 5], active=[5, 7, 1400], equations=[], phase=[], scalar=[3, 11]))
    for k in (1, 12, 64):
        request = wide_pair_request(k)
        expected = dict(n=request['n'], retained=request['retained'], zero=False, equations=[],
                        phase=sorted((1 << (4*i+2)) | (1 << (4*i+3)) for i in range(k)),
                        scalar=[-3*(1 << k), 7], free_ids=request['retained'])
        add('wide_pair_'+str(k), request, expected)
    k = 96
    request = dict(n=2*k, retained=list(range(k, 2*k)), equations=[],
                   phase=[(1 << i) | (1 << (k+i)) for i in range(k)], scalar=1)
    expected = dict(n=2*k, retained=request['retained'], zero=False,
                    equations=[[1 << i, 0] for i in request['retained']], phase=[], scalar=[1 << k, 1], free_ids=[])
    add('wide_boundary_pins_96', request, expected)
    add('derived_row_cap', request, caps={'max_rows': 50})
    add('work_cap', wide_pair_request(12), caps={'max_work': 0})
    add('scalar_bit_cap', wide_pair_request(12), caps={'max_scalar_bits': 3})
    request = dict(n=320, retained=list(range(256, 320)), equations=[], phase=[], scalar=[1, 5])
    expected = dict(n=320, retained=request['retained'], zero=False, equations=[], phase=[],
                    scalar=[1 << 256, 5], free_ids=request['retained'])
    add('unused_256_internal_bits', request, expected)
    rng = random.Random(19102688)
    for case in range(60):
        n = rng.randrange(9)
        active = [v for v in range(n) if rng.randrange(4)]
        rng.shuffle(active)
        retained = [v for v in active if rng.randrange(2)]
        rng.shuffle(retained)
        rows = [[sum(1 << v for v in active if rng.randrange(2)), rng.randrange(2)] for _ in range(rng.randrange(5))]
        terms = [0]+[1 << v for v in active]+[(1 << a) | (1 << b) for a, b in combinations(active, 2)]
        phase = [t for t in terms if rng.randrange(2)]
        scalar = pair(Fraction(rng.choice([-3, -1, 0, 1, 5]), rng.choice([1, 2, 7])))
        add('seeded_'+str(case), dict(n=n, retained=retained, active=active, equations=rows, phase=phase, scalar=scalar))
    end_hashes = source_hashes()
    assert end_hashes == start_hashes
    result = dict(schema='block-affine-boundary-reference-v1', source_sha256=end_hashes,
                  source_unchanged_during_run=True, cases=cases,
                  summary=dict(cases=len(cases), statuses=dict(Counter(c['result']['status'] for c in cases)),
                               original_assignment_checks=choices, exhaustive_test_requests=4718,
                               seeded_test_requests=400, one_bit_crosschecks=220,
                               largest_wide_boundary_bits=128))
    (HERE/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    run()
