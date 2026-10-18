"""Independent replay of explicit concatenated-code certificates."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import (
    field_modulus, gf_mul, irreducible, parameters, random_transforms,
    upper_transform, verify_sampled_transforms,
)

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def replay_formula(k):
    q = 1 << k
    t = q // (k * k)
    r = k * t
    budget = 1 + r + r * (r - 1) // 2
    distance = (q - t + 1) * (q // 2)
    return {'field_degree': k, 'field_size': q, 'polynomial_degree': t,
            'binary_rank': r, 'columns': q * (q - 1),
            'minimum_code_distance': distance,
            'low_weight_budget': budget, 'state_lower_bound': 1 << r}


def exhaustive_linear_case_weight():
    """For k=7,t=2, enumerate every nonzero linear polynomial."""
    k, q = 7, 1 << 7
    modulus = field_modulus(k)
    minimum = None
    for coefficient0 in range(q):
        for coefficient1 in range(q):
            if coefficient0 == coefficient1 == 0:
                continue
            roots = 0
            for evaluation in range(q):
                value = coefficient0 ^ gf_mul(coefficient1, evaluation, modulus, k)
                roots += value == 0
            weight = (q - roots) * (q // 2)
            minimum = weight if minimum is None else min(minimum, weight)
    return minimum


def mul2(a, b, modulus, degree):
    result = 0
    for _ in range(degree * 2):
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << degree):
            a ^= modulus
    return result & ((1 << degree) - 1)


def trace2(value, modulus, degree):
    result = 0
    for _ in range(degree):
        result ^= value
        value = mul2(value, value, modulus, degree)
    assert result in (0, 1)
    return result


def independent_columns(k, modulus):
    q = 1 << k
    t = q // (k * k)
    dual = tuple(sum(trace2(mul2(value, 1 << bit, modulus, k), modulus, k) << bit
                     for bit in range(k)) for value in range(q))
    columns = []
    for evaluation in range(q):
        powers = [1]
        for _ in range(1, t):
            powers.append(mul2(powers[-1], evaluation, modulus, k))
        for beta in range(1, q):
            column = 0
            for coefficient, power in enumerate(powers):
                column |= dual[mul2(beta, power, modulus, k)] << (coefficient * k)
            columns.append(column)
    return tuple(columns)


def rank2(values):
    pivots = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def independent_stats(columns, transform):
    transformed = []
    for column in columns:
        output = 0
        for row, mask in enumerate(transform):
            output |= ((mask & column).bit_count() & 1) << row
        transformed.append(output)
    exceptional = [value for value in transformed if value.bit_count() > 2]
    return [len(exceptional), rank2(exceptional),
            sum(max(0, value.bit_count() - 2) for value in transformed),
            sum(value.bit_count() for value in transformed)]


def run():
    payload = json.loads((HERE / 'EXPLICIT_CODE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'EXPLICIT_CODE_FAMILY_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]
    assert payload['source_hash'] == digest(HERE / 'explicit_code_family.py')
    reviewed = []
    for saved in payload['records']:
        k = saved['parameters']['field_degree']
        expected = replay_formula(k)
        assert saved['parameters'] == expected
        assert expected == parameters(k)
        modulus = field_modulus(k)
        assert saved['field_modulus'] == modulus and irreducible(modulus, k)
        assert expected['minimum_code_distance'] > expected['low_weight_budget']
        replay = verify_sampled_transforms(k, transform_count=6)
        assert replay['column_digest'] == saved['column_digest']
        assert replay['sampled_stats'] == saved['sampled_stats']
        assert replay['distinct_columns'] == expected['columns']
        independent = independent_columns(k, modulus)
        assert len(independent) == expected['columns']
        assert len(set(independent)) == expected['columns']
        transforms = (tuple(1 << row for row in range(expected['binary_rank'])),
                      upper_transform(expected['binary_rank']),
                      *random_transforms(expected['binary_rank'], 6, 20261018 + k))
        independent_records = []
        for transform in transforms:
            stats = independent_stats(independent, transform)
            independent_records.append({'exceptional_count': stats[0],
                                        'exceptional_rank': stats[1],
                                        'excess': stats[2], 'total': stats[3]})
        assert independent_records == saved['sampled_stats']
        reviewed.append({'k': k, 'rank': expected['binary_rank'],
                         'columns': expected['columns'],
                         'states': expected['state_lower_bound']})
    linear_minimum = exhaustive_linear_case_weight()
    assert linear_minimum == 8128
    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'run_explicit_code_family.py',
               'EXPLICIT_CODE_FAMILY_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_EXPLICIT_CODE_FAMILY',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'rank7_states': 1 << 14,
        'rank8_states': 1 << 32,
        'rank9_states': 1 << 54,
        'k7_exhaustive_minimum_distance': linear_minimum,
        'source_hashes': source,
        'scope': 'Independent formula, field, distinctness and sampled-basis replay; route-specific only.',
    }
    (HERE / 'EXPLICIT_CODE_FAMILY_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'EXPLICIT_CODE_FAMILY_REVIEW.md').write_text(
        '# Independent explicit-code review\n\n'
        'The deterministic trace/Reed--Solomon construction is replayed at '
        'k=7, 8 and 9. A second field/trace/column implementation independently '
        'reproduces the hashes and sampled transformed statistics. Field '
        'irreducibility, column distinctness and distance bounds all agree. The '
        'forced state lower bounds are 2^14, 2^32 and 2^54. An exhaustive '
        'enumeration of all 16,383 nonzero degree-one messages at k=7 also '
        'attains the predicted minimum distance 8,128. This is a lower bound '
        'for one representation route, not a P-versus-NP proof.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'states': [review['rank7_states'], review['rank8_states'], review['rank9_states']]}))


if __name__ == '__main__':
    run()
