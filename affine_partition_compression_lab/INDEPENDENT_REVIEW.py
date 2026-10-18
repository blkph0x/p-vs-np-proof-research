"""Independent finite-set/ANF audit plus frozen block-norm proof replay."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


producer = load('independently_reviewed_partition', HERE/'partition.py')
oracle = load('partition_independent_block_oracle', NIGHT/'affine_compression_review'/'review_oracles.py')


def evaluate(message, word):
    if message['zero']:
        return Fraction(0)
    if any((word & mask).bit_count() % 2 != rhs for mask, rhs in message['equations']):
        return Fraction(0)
    sign = sum((word & mask) == mask for mask in message['phase']) % 2
    return Fraction(*message['scalar'])*(-1 if sign else 1)


def words(ids):
    return [sum(((bits >> i) & 1) << v for i, v in enumerate(ids)) for bits in range(1 << len(ids))]


def classify(ids, messages):
    """Finite supports and full Mobius ANF, not producer hull/phase fitting."""
    assignments = words(ids)
    nonzero = [m for m in messages if not m['zero']]
    values = {word: sum((evaluate(m, word) for m in messages), Fraction(0)) for word in assignments}
    if not nonzero:
        return 'EXACT', None, values
    magnitudes = {abs(Fraction(*m['scalar'])) for m in nonzero}
    if len(magnitudes) != 1:
        return 'UNSUPPORTED', 'unequal magnitudes', values
    supports = [{word for word in assignments if evaluate(m, word)} for m in nonzero]
    if any(a & b for a, b in itertools.combinations(supports, 2)):
        return 'UNSUPPORTED', 'overlapping supports', values
    union = set().union(*supports)
    assert union
    anchor = min(union)
    reduced, directions = {}, []
    for point in sorted(union):
        original = point ^ anchor
        value = original
        while value:
            bit = value.bit_length()-1
            if bit in reduced:
                value ^= reduced[bit]
            else:
                reduced[bit] = value
                directions.append(original)
                break
    if len(union) != 1 << len(directions):
        return 'UNSUPPORTED', 'gap in affine hull', values
    magnitude = next(iter(magnitudes))
    truth = []
    for bits in range(1 << len(directions)):
        word = anchor
        for j, direction in enumerate(directions):
            if (bits >> j) & 1:
                word ^= direction
        value = values[word]
        assert value in (magnitude, -magnitude)
        truth.append(int(value == -magnitude))
    for j in range(len(directions)):
        for bits in range(len(truth)):
            if (bits >> j) & 1:
                truth[bits] ^= truth[bits ^ (1 << j)]
    if any(coefficient and monomial.bit_count() > 2 for monomial, coefficient in enumerate(truth)):
        return 'UNSUPPORTED', 'incompatible quadratic phase', values
    return 'EXACT', None, values


def hashes():
    paths = [HERE/name for name in ('partition.py', 'controls.py', 'test_partition.py',
              'THEOREM.md', 'RESULTS.json', 'INDEPENDENT_REVIEW.py')]
    paths += [NIGHT/'affine_compression_review'/'review_oracles.py',
              NIGHT/'affine_boundary_reference'/'reference.py']
    return {str(p.relative_to(NIGHT)).replace('\\', '/'): sha256(p.read_bytes()).hexdigest() for p in paths}


def equations_for_points(ids, points):
    rows = []
    for mask in words(ids)[1:]:
        outcomes = {(mask & word).bit_count() % 2 for word in points}
        if len(outcomes) == 1:
            rows.append([mask, outcomes.pop()])
    return rows


def new_requests(seed=2026101863, count=100):
    rng = random.Random(seed)
    for index in range(count):
        n = 11
        ids = rng.sample(range(n), rng.randrange(2, 7))
        dimension = rng.randrange(1, len(ids)+1)
        directions = [1 << i for i in range(len(ids))]
        for _ in range(12):
            i, j = rng.sample(range(len(ids)), 2)
            directions[j] ^= directions[i]
        directions = [sum(((direction >> j) & 1) << v for j, v in enumerate(ids)) for direction in directions[:dimension]]
        anchor = rng.choice(words(ids))
        leaves = [{}]
        for _ in range(rng.randrange(1, 7)):
            possible = [i for i, leaf in enumerate(leaves) if len(leaf) < dimension]
            if not possible:
                break
            leaf = leaves.pop(rng.choice(possible))
            bit = rng.choice([j for j in range(dimension) if j not in leaf])
            leaves += [{**leaf, bit: 0}, {**leaf, bit: 1}]
        phase = [0] if rng.randrange(2) else []
        phase += [1 << v for v in ids if rng.randrange(2)]
        phase += [(1 << u) | (1 << v) for u, v in itertools.combinations(ids, 2) if rng.randrange(2)]
        scale = Fraction(rng.choice((-5, -1, 1, 3)), rng.choice((1, 3, 7)))
        messages = []
        for leaf in leaves:
            points = []
            for bits in range(1 << dimension):
                if any(((bits >> j) & 1) != value for j, value in leaf.items()):
                    continue
                word = anchor
                for j, direction in enumerate(directions):
                    if (bits >> j) & 1:
                        word ^= direction
                points.append(word)
            local_scale = -scale if index % 2 and rng.randrange(2) else scale
            messages.append(oracle.canonical(n, ids, equations_for_points(ids, points), phase, local_scale))
        if index % 3 == 0:
            messages.insert(rng.randrange(len(messages)+1), oracle.canonical(n, ids, scalar=0))
        rng.shuffle(messages)
        yield dict(index=index, n=n, retained=ids, messages=messages)


def run():
    before = hashes()
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    for path, expected in saved['source_hashes_after'].items():
        assert sha256((NIGHT/path).read_bytes()).hexdigest() == expected, path
    cases = sum((saved[key] for key in ('named_controls', 'all_three_bit_affine_partitions',
                                       'all_three_bit_sign_tables', 'seeded_partitions')), [])
    totals = Counter()
    unsupported = Counter()
    norm_records = []
    for index, case in enumerate(cases):
        request, result = case['original_request'], case['result']
        n, ids, messages = request['n'], request['retained'], request['messages']
        totals['saved_cases'] += 1
        totals[result['status']] += 1
        if result['status'] == 'EXACT':
            check = producer.verify_partition(n, ids, messages, result, **request.get('caps', {}))
            assert check['valid'], (index, check)
            totals['exact_certificates_replayed'] += 1
        else:
            assert result['message'] is None and result['certificate'] is None
        if len(ids) <= 8 and result['status'] != 'UNKNOWN':
            expected, reason, values = classify(ids, messages)
            assert result['status'] == expected, (index, reason, result)
            totals['independent_status_classifications'] += 1
            totals['original_assignments'] += len(values)
            if expected == 'UNSUPPORTED':
                assert result['reason'] == reason
                unsupported[reason] += 1
            else:
                assert all(evaluate(result['message'], word) == value for word, value in values.items())
        if 'norm_certificate' in case:
            check = oracle.verify_norm_identity(n, ids, messages, [result['message']], case['norm_certificate'])
            assert check['valid'] and check['equal']
            totals['saved_norms_replayed'] += 1
            totals['saved_norm_products'] += case['norm_certificate']['block_checks']
            norm_records.append(dict(case_index=index, verification=check))
    additional = []
    for request in new_requests():
        n, ids, messages = request['n'], request['retained'], request['messages']
        expected, reason, values = classify(ids, messages)
        result = producer.recognize(n, ids, messages)
        assert result['status'] == expected, (request, reason, result)
        checked = None
        if expected == 'EXACT':
            checked = producer.verify_partition(n, ids, messages, result)
            assert checked['valid']
            assert all(evaluate(result['message'], word) == value for word, value in values.items())
        else:
            assert result['reason'] == reason
        totals['additional_cases'] += 1
        totals['additional_'+expected] += 1
        totals['additional_assignments'] += len(values)
        additional.append(dict(original_request=request, independent_status=expected,
                               independent_reason=reason, result=result, verification=checked))
    # Original n bounds positions but never introduces unretained free factors.
    ids = [99, 3]
    messages = [oracle.canonical(100, ids, [[1 << 99, bit]]) for bit in (0, 1)]
    sparse = producer.recognize(100, ids, messages)
    assert sparse['status'] == 'EXACT' and sparse['message']['scalar'] == [1, 1]
    assert producer.verify_partition(100, ids, messages, sparse)['valid']
    sparse_norm = oracle.norm_identity(100, ids, messages, [sparse['message']], save_proofs=True)
    sparse_check = oracle.verify_norm_identity(100, ids, messages, [sparse['message']], sparse_norm)
    assert sparse_check['valid'] and sparse_check['equal']
    # Explicit rational bit thresholds, with no floating point or coordinate expansion.
    bits = []
    for scale in (Fraction(1 << 70, 3), Fraction(-1, 1 << 70)):
        pieces = [oracle.canonical(4, [3, 1], [[8, bit]], scalar=scale) for bit in (0, 1)]
        low = producer.recognize(4, [3, 1], pieces, max_scalar_bits=70)
        high = producer.recognize(4, [3, 1], pieces, max_scalar_bits=71)
        assert low['status'] == 'UNKNOWN' and low['message'] is None
        assert high['status'] == 'EXACT' and producer.verify_partition(4, [3, 1], pieces, high, max_scalar_bits=71)['valid']
        bits.append(dict(originals=pieces, rejected_budget=low, accepted_budget=high))
    # Malformed original coordinate/type controls must fail before recognition.
    rejected = []
    for field, change in [('phase_outside_retained', lambda m: m.__setitem__('phase', [2])),
                          ('boolean_free_id', lambda m: m['free_ids'].__setitem__(0, True)),
                          ('float_scalar', lambda m: m.__setitem__('scalar', [1.0, 1])),
                          ('false_zero_flag', lambda m: m.__setitem__('zero', True))]:
        malformed = deepcopy(messages)
        change(malformed[0])
        try:
            producer.recognize(100, ids, malformed)
        except ValueError:
            rejected.append(field)
        else:
            raise AssertionError(field)
    assert len(rejected) == 4
    after = hashes()
    assert before == after
    report = dict(format='independent-affine-partition-review-v1',
        timestamp_utc=datetime.now(timezone.utc).isoformat(), source_hashes_before=before,
        source_hashes_after=after, sources_unchanged_during_review=True,
        totals=dict(totals), unsupported_reason_checks=dict(unsupported),
        saved_norm_replays=norm_records, additional_cases=additional,
        sparse_original_request=dict(n=100, retained=ids, messages=messages), sparse_result=sparse,
        sparse_norm=sparse_norm, sparse_norm_verification=sparse_check,
        rational_bit_controls=bits, rejected_malformed_originals=rejected,
        resource_cap_repair=dict(
            before_core_sha256='d4754df367da2b828b85642788460fcdf38bd176d09f7a3f8833c2c30a01dac8',
            after_core_sha256=before['affine_partition_compression_lab/partition.py'],
            finding='The quadratic monomial list was allocated before checking its D-coefficient cap.',
            repair='Preflight D=1+d+d*(d-1)//2 before allocation; preserve existing operation counters.',
            regression='Mock combinations to fail if reached when D exceeds the cap; also check the exact D=7 acceptance boundary.',
            scope='Resource-cap ordering only; no mathematical decision or existing operation-unit change.'),
        finding='No correctness or scope defect found. UNSUPPORTED is narrow recognition failure, not an arbitrary-sum impossibility proof.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'totals': report['totals'], 'unsupported': report['unsupported_reason_checks']}, indent=2))


if __name__ == '__main__':
    run()
