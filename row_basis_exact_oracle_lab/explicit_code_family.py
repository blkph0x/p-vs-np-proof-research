"""Explicit concatenated-code family forcing full exceptional rank.

The construction uses Reed--Solomon evaluation over GF(2^k), followed by the
binary trace map y -> (Tr(beta*y)) for every nonzero beta.  It is kept separate
from the probabilistic bound so its finite certificates can be replayed.
"""

from __future__ import annotations

from hashlib import sha256
import random

from exact_oracle import rank


def poly_mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
    return result


def poly_mod(value, modulus):
    degree = modulus.bit_length() - 1
    while value and value.bit_length() - 1 >= degree:
        value ^= modulus << (value.bit_length() - 1 - degree)
    return value


def poly_gcd(a, b):
    while b:
        a, b = b, poly_mod(a, b)
    return a


def poly_square_mod(value, modulus):
    return poly_mod(poly_mul(value, value), modulus)


def irreducible(modulus, degree):
    """Rabin irreducibility test for a monic binary polynomial."""
    x = 2
    value = x
    for step in range(1, degree + 1):
        value = poly_square_mod(value, modulus)
        if step <= degree // 2 and poly_gcd(value ^ x, modulus) != 1:
            return False
    return value == x


def field_modulus(degree):
    if type(degree) is not int or degree < 2:
        raise ValueError('field degree must be at least two')
    for lower in range(1, 1 << degree, 2):
        candidate = (1 << degree) | lower
        if irreducible(candidate, degree):
            return candidate
    raise ArithmeticError('no irreducible polynomial found')


def gf_mul(a, b, modulus, degree):
    result = 0
    mask = (1 << degree) - 1
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << degree):
            a ^= modulus
    return result & mask


def gf_trace(value, modulus, degree):
    result = 0
    power = value
    for _ in range(degree):
        result ^= power
        power = gf_mul(power, power, modulus, degree)
    if result not in (0, 1):
        raise ArithmeticError('trace did not land in the prime field')
    return result


def parameters(degree):
    k = degree
    q = 1 << k
    t = q // (k * k)
    if t < 2:
        raise ValueError('degree is too small for the explicit family')
    r = k * t
    low_weight = 1 + r + r * (r - 1) // 2
    distance = (q - t + 1) * (q // 2)
    if distance <= low_weight:
        raise ArithmeticError('distance does not beat the low-weight budget')
    return {'field_degree': k, 'field_size': q, 'polynomial_degree': t,
            'binary_rank': r, 'columns': q * (q - 1),
            'minimum_code_distance': distance,
            'low_weight_budget': low_weight,
            'state_lower_bound': 1 << r}


def dual_masks(modulus, degree):
    q = 1 << degree
    return tuple(sum(gf_trace(gf_mul(value, 1 << bit, modulus, degree), modulus, degree) << bit
                     for bit in range(degree)) for value in range(q))


def generate_columns(degree):
    k = degree
    spec = parameters(k)
    q, t = spec['field_size'], spec['polynomial_degree']
    modulus = field_modulus(k)
    dual = dual_masks(modulus, k)
    columns = []
    for evaluation in range(q):
        powers = [1]
        for _ in range(1, t):
            powers.append(gf_mul(powers[-1], evaluation, modulus, k))
        for beta in range(1, q):
            column = 0
            for coefficient, power in enumerate(powers):
                column |= dual[gf_mul(beta, power, modulus, k)] << (coefficient * k)
            columns.append(column)
    if len(columns) != spec['columns'] or len(set(columns)) != len(columns):
        raise ArithmeticError('explicit columns are not distinct')
    return modulus, tuple(columns)


def transform_columns(columns, transform):
    return tuple(sum(((mask & column).bit_count() & 1) << row
                     for row, mask in enumerate(transform)) for column in columns)


def column_stats(columns, rank_value):
    exceptional = [column for column in columns if column.bit_count() > 2]
    return (len(exceptional), rank(exceptional),
            sum(max(0, column.bit_count() - 2) for column in columns),
            sum(column.bit_count() for column in columns))


def upper_transform(rank_value):
    return tuple((1 << row) | ((1 << (row + 1)) if row + 1 < rank_value else 0)
                 for row in range(rank_value))


def random_transforms(rank_value, count, seed):
    rng = random.Random(seed)
    transforms = []
    for _ in range(count):
        current = [1 << row for row in range(rank_value)]
        for _ in range(3 * rank_value):
            destination = rng.randrange(rank_value)
            source = rng.randrange(rank_value - 1)
            if source >= destination:
                source += 1
            current[destination] ^= current[source]
        if rank(current) != rank_value:
            raise ArithmeticError('elementary transform became singular')
        transforms.append(tuple(current))
    return tuple(transforms)


def digest_columns(columns, rank_value):
    width = (rank_value + 7) // 8
    digest = sha256()
    for column in columns:
        digest.update(column.to_bytes(width, 'little'))
    return digest.hexdigest()


def verify_sampled_transforms(degree, transform_count=6):
    spec = parameters(degree)
    modulus, columns = generate_columns(degree)
    transforms = (tuple(1 << row for row in range(spec['binary_rank'])),
                  upper_transform(spec['binary_rank']),
                  *random_transforms(spec['binary_rank'], transform_count, 20261018 + degree))
    stats = []
    for transform in transforms:
        if rank(transform) != spec['binary_rank']:
            raise ArithmeticError('singular sampled transform')
        transformed = transform_columns(columns, transform)
        observed = column_stats(transformed, spec['binary_rank'])
        if observed[1] != spec['binary_rank']:
            raise AssertionError('sampled basis lost exceptional rank')
        stats.append({'exceptional_count': observed[0],
                      'exceptional_rank': observed[1],
                      'excess': observed[2], 'total': observed[3]})
    return {'parameters': spec, 'field_modulus': modulus,
            'column_digest': digest_columns(columns, spec['binary_rank']),
            'distinct_columns': len(columns), 'transform_count': len(transforms),
            'sampled_stats': stats}
