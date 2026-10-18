"""Root review: direct original assignment sums, without algebra helpers."""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from reference import marginalize_reference, verify_reference

HERE = Path(__file__).resolve().parent
SOURCES = ['reference.py', 'test_reference.py', 'THEOREM.md', 'run_experiments.py',
           'RESULTS.json', 'independent_review.py']


def hashes():
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def value(word, rows, phase, scalar):
    if any((word & mask).bit_count() % 2 != rhs for mask, rhs in rows):
        return Fraction(0)
    sign = sum((word & mask) == mask for mask in phase) % 2
    return scalar*(-1 if sign else 1)


def direct(request):
    active = request.get('active', list(range(request['n'])))
    retained = request['retained']
    scale = request['scalar']
    scale = Fraction(*scale) if isinstance(scale, (list, tuple)) else Fraction(scale)
    answer = [Fraction(0) for _ in range(1 << len(retained))]
    for packed in range(1 << len(active)):
        word = sum(((packed >> j) & 1) << v for j, v in enumerate(active))
        index = sum(((word >> v) & 1) << j for j, v in enumerate(retained))
        answer[index] += value(word, request['equations'], request['phase'], scale)
    return answer


def reported(request, message):
    answer = []
    for packed in range(1 << len(request['retained'])):
        word = sum(((packed >> j) & 1) << v for j, v in enumerate(request['retained']))
        answer.append(Fraction(0) if message['zero'] else value(word, message['equations'],
                      message['phase'], Fraction(*message['scalar'])))
    return answer


def main():
    before = hashes()
    rng = random.Random(2026101803)
    counts = dict(random_original_requests=0, original_assignment_words=0,
                  complete_boundary_values=0, saved_exact_proofs=0, saved_unknown=0,
                  rejected_mutations=0)
    for _ in range(500):
        n = rng.randrange(10)
        active = [v for v in range(n) if rng.randrange(4)]
        rng.shuffle(active)
        retained = [v for v in active if rng.randrange(2)]
        rng.shuffle(retained)
        allowed = sum(1 << v for v in active)
        rows = [[rng.getrandbits(n) & allowed, rng.randrange(2)] for _ in range(rng.randrange(6))]
        terms = [0]+[1 << v for v in active]+[(1 << u) | (1 << v) for i, u in enumerate(active) for v in active[i+1:]]
        phase = [rng.choice(terms) for _ in range(rng.randrange(15))]
        request = dict(n=n, active=active, retained=retained, equations=rows, phase=phase,
                       scalar=rng.choice(([0, 1], [1, 1], [-1, 1], [2, 3], [-5, 7])))
        result = marginalize_reference(**request)
        assert result['status'] == 'EXACT'
        assert verify_reference(**request, result=result)['valid']
        assert direct(request) == reported(request, result['message'])
        counts['random_original_requests'] += 1
        counts['original_assignment_words'] += 1 << len(active)
        counts['complete_boundary_values'] += 1 << len(retained)
        bad = copy.deepcopy(result)
        if bad['message']['zero']:
            bad['message'].update(zero=False, equations=[], phase=[], scalar=[1, 1], free_ids=retained)
        else:
            bad['message']['scalar'][0] *= 2
        assert not verify_reference(**request, result=bad)['valid']
        counts['rejected_mutations'] += 1
        changed = dict(request, scalar=[11, 13])
        assert not verify_reference(**changed, result=result)['valid']
        counts['rejected_mutations'] += 1
        if result['certificate']['kind'] == 'block-pair':
            bad = copy.deepcopy(result)
            bad['certificate']['factor_power'] += 1
            assert not verify_reference(**request, result=bad)['valid']
            counts['rejected_mutations'] += 1
            if result['certificate']['pairs']:
                bad = copy.deepcopy(result)
                bad['certificate']['pairs'][0]['after'].append(0)
                assert not verify_reference(**request, result=bad)['valid']
                counts['rejected_mutations'] += 1
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    for case in saved['cases']:
        if case['result']['status'] == 'EXACT':
            assert verify_reference(**case['request'], result=case['result'], **case['caps'])['valid']
            counts['saved_exact_proofs'] += 1
            if len(case['request'].get('active', list(range(case['request']['n'])))) <= 10:
                assert direct(case['request']) == reported(case['request'], case['result']['message'])
        else:
            assert case['result']['status'] == 'UNKNOWN'
            counts['saved_unknown'] += 1
    assert before == hashes()
    out = dict(status='PASS', source_sha256=before, sources_unchanged_during_review=True,
               counts=counts, findings=[],
               proof_review='Projected support is tested by the full left nullspace. Injectivity plus checked nullity gives all internal solutions; pair identities and residual linear constraints preserve signed multiplicity.',
               limitation='Code and ordinary mathematical argument review, not proof-assistant formalization or evidence resolving P versus NP.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
