"""Finite reproducible controls; all full input/output proofs are saved."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import random
import time
import compression as c

HERE = Path(__file__).resolve().parent
SOURCES = ['compression.py', 'test_compression.py', 'run_experiments.py', 'THEOREM.md',
           '../affine_boundary_lab/boundary.py', '../AFFINE_SUM_COMPRESSION_NEXT.md']


def hashes():
    return {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def piece(n, retained=None, rows=(), phase=(), scalar=1):
    retained = list(range(n)) if retained is None else retained
    result = c.boundary.normalize_message(n, retained, list(rows), list(phase), scalar)
    assert result['status'] == 'EXACT'
    return result['message']


def evaluate(message, word):
    if message['zero'] or any((word & mask).bit_count() % 2 != rhs for mask, rhs in message['equations']):
        return Fraction(0)
    return Fraction(*message['scalar']) * (-1) ** (sum(word & term == term for term in message['phase']) % 2)


def main():
    before = hashes(); controls = []; totals = dict(EXACT=0, UNKNOWN=0, assignment_checks=0, explicit_symbolic_controls=0)
    def add(name, n, originals, retained=None, expected=None, **caps):
        retained = list(range(n)) if retained is None else retained
        started = time.perf_counter(); result = c.compress(n, retained, originals, **caps)
        producer_seconds = time.perf_counter()-started
        record = dict(name=name, n=n, retained=retained, originals=originals, caps=caps, result=result, producer_seconds=producer_seconds)
        totals[result['status']] += 1
        if result['status'] == 'EXACT':
            started = time.perf_counter(); checked = c.verify_compression(n, retained, originals, result)
            assert checked['valid'], checked
            record['verification'] = checked; record['verification_seconds'] = time.perf_counter()-started
            if len(retained) <= 8:
                for bits in range(1 << len(retained)):
                    word = sum(((bits >> j) & 1) << i for j, i in enumerate(retained))
                    assert sum(evaluate(p, word) for p in originals) == sum(evaluate(p, word) for p in checked['messages'])
                record['independent_assignment_checks'] = 1 << len(retained)
                totals['assignment_checks'] += 1 << len(retained)
            if expected is not None:
                assert checked['messages'] == expected
                record['algebraic_expected_messages'] = expected
                totals['explicit_symbolic_controls'] += 1
        else:
            assert result['messages'] is None and result['certificate'] is None
        controls.append(record)

    add('empty_sum', 0, [])
    add('zero_input', 3, [piece(3, scalar=0)])
    add('rational_identical_addition', 3, [piece(3, rows=[[3, 1]], phase=[4], scalar=Fraction(2, 3)), piece(3, rows=[[3, 1]], phase=[4], scalar=Fraction(-5, 7))])
    add('exact_cancellation', 2, [piece(2, scalar=Fraction(3, 7)), piece(2, scalar=Fraction(-3, 7))])
    add('same_support_affine_pin', 4, [piece(4, phase=[12]), piece(4, phase=[12, 1, 2], scalar=-1)])
    add('parallel_signed_union', 4, [piece(4, rows=[[1, 0]], phase=[12]), piece(4, rows=[[1, 1]], phase=[12, 2], scalar=-1)])
    add('nested_effective_restricted_sign', 3, [piece(3, phase=[3]), piece(3, rows=[[1, 1]], phase=[2], scalar=-1)])
    add('nested_wrong_effective_sign_refused', 3, [piece(3, phase=[3]), piece(3, rows=[[1, 1]], phase=[2], scalar=1)])
    add('nested_constant_one_after_restriction', 3, [piece(3, phase=[1]), piece(3, rows=[[1, 1]])])
    add('unequal_magnitudes_refused', 2, [piece(2, rows=[[1, 0]]), piece(2, rows=[[1, 1]], scalar=2)])
    add('quadratic_difference_refused', 3, [piece(3, rows=[[1, 0]]), piece(3, rows=[[1, 1]], phase=[6])])
    add('higher_codimension_refused', 3, [piece(3), piece(3, rows=[[1, 0], [2, 0]], scalar=-1)])
    pins = [piece(3, rows=[[1 << i, word >> i & 1] for i in range(3)]) for word in range(8)]
    add('natural_order_one_piece', 3, pins)
    add('nonconfluent_order_four_pieces', 3, [pins[i] for i in [0, 1, 4, 6, 3, 7, 2, 5]])
    add('retained_cap_one_actual_live_two_pending_three', 1, [piece(1), piece(1)], max_live_pieces=1)
    add('sparse_permuted_original_coordinates', 9, [piece(9, [8, 0, 3], [[257, 0]], [8]), piece(9, [8, 0, 3], [[257, 1]], [8])], retained=[8, 0, 3])
    for n in [64, 256, 512]:
        phase = [(1 << i) | (1 << (i+1)) for i in range(2, n, 2)]
        add(f'wide_parallel_{n}', n, [piece(n, rows=[[1, 0]], phase=phase), piece(n, rows=[[1, 1]], phase=phase+[2])], expected=[piece(n, phase=phase+[3])])
        add(f'wide_nested_{n}', n, [piece(n, phase=[3]+phase), piece(n, rows=[[1, 1]], phase=[2]+phase, scalar=-1)], expected=[piece(n, rows=[[1, 0]], phase=phase)])
    for cap in ['max_inputs', 'max_generated', 'max_pairs', 'max_steps', 'max_work', 'max_live_pieces', 'max_scalar_bits']:
        add('exhaust_'+cap, 1, [piece(1), piece(1)], **{cap: 0})
    rng = random.Random(2026101908)
    for number in range(80):
        n = rng.randrange(7)
        terms = [1 << i for i in range(n)] + [(1 << i) | (1 << j) for i in range(n) for j in range(i+1, n)]
        originals = [piece(n, rows=[[rng.getrandbits(n), rng.randrange(2)] for _ in range(rng.randrange(4))],
                           phase=rng.sample(terms, rng.randrange(len(terms)+1)), scalar=Fraction(rng.randrange(-4, 5), rng.randrange(1, 6)))
                     for _ in range(rng.randrange(9))]
        add(f'seeded_{number:02d}', n, originals)
    after = hashes(); assert after == before
    result = dict(scope='Finite exact local rewrites; no confluence, optimum-size or general SAT complexity claim.',
                  seed=2026101908, source_sha256=before, source_unchanged_during_run=True, totals=totals,
                  test_command='python -m unittest -v test_compression', controls=controls)
    (HERE/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    lines = ['# Affine sum compression controls', '',
             f"Saved {len(controls)} original requests: {totals['EXACT']} EXACT with independently replayed certificates and {totals['UNKNOWN']} UNKNOWN with no output sum.",
             f"Bounded direct comparison checked {totals['assignment_checks']} assignments; {totals['explicit_symbolic_controls']} wide requests matched explicit algebraic expected messages.", '',
             'The natural singleton order produces one piece; the recorded adverse order produces four. Settled cap one on two identical pieces reports actual live peak two and live-plus-pending peak three.', '',
             'Producer and verifier operation counts and timings are separate in RESULTS.json. The certificate proves sum equality, not irreducibility. All six source references were unchanged during the run.', '',
             '| Control | Status | Incoming | Final | Live peak | Retained peak | Producer work | Verifier work |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for item in controls[:28]:
        r = item['result']; s = r['stats']; v = item.get('verification', {}).get('stats', {})
        lines.append(f"| {item['name']} | {r['status']} | {len(item['originals'])} | {len(r['messages']) if r['messages'] is not None else '-'} | {s['peak_live_pieces']} | {s['peak_retained_pieces']} | {s['work']} | {v.get('work', '-')} |")
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(dict(requests=len(controls), **totals, source_unchanged_during_run=True)))


if __name__ == '__main__':
    main()
