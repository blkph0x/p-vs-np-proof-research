"""Representation-count bounds, not lower bounds for general SAT algorithms."""
from itertools import combinations


def gaussian_row(n):
    if type(n) is not int or n < 0:
        raise ValueError('nonnegative dimension required')
    row = [1]
    for m in range(1, n+1):
        row = [(row[d] if d < m else 0) + ((1 << (m-d))*row[d-1] if d else 0)
               for d in range(m+1)]
    return row


def dictionary_count(n):
    return sum(g*(1 << (n-d+d*(d+1)//2)) for d, g in enumerate(gaussian_row(n)))


def dictionary_product(n):
    if type(n) is not int or n < 0:
        raise ValueError('nonnegative dimension required')
    value = 1 << n
    for i in range(n):
        value *= 1+(1 << i)
    return value


def existence_bound(n):
    directions = dictionary_count(n)
    # D+1 possibilities per padded tuple position, including the zero direction.
    # D.bit_length() equals ceil(log2(D+1)) for positive integer D.
    per_piece_exponent_bound = 1+directions.bit_length()
    excluded_k = ((1 << n)-1)//per_piece_exponent_bound
    return dict(n=n, dictionary_directions=directions,
                per_piece_exponent_bound=per_piece_exponent_bound,
                some_boolean_function_requires_at_least=excluded_k+1,
                all_boolean_functions_representable_with=1 << n,
                scope='arbitrary Boolean truth functions; no succinct-CNF or algorithmic lower bound')


def enumerate_directions(n, max_n=4):
    """Independent exhaustive truth-table oracle; exponential and hard-capped."""
    if type(n) is not int or not 0 <= n <= max_n:
        raise ValueError('explicit dictionary enumeration cap')
    points = 1 << n
    monomials = [1 << i for i in range(n)]+[(1 << i) | (1 << j) for i, j in combinations(range(n), 2)]
    phase_masks = [0]
    for monomial in monomials:
        truth = sum(1 << x for x in range(points) if x & monomial == monomial)
        phase_masks += [word ^ truth for word in phase_masks]
    directions = set()
    supports = 0
    for support in range(1, 1 << points):
        anchor = (support & -support).bit_length()-1
        affine = [x for x in range(points) if support >> x & 1]
        translated = {x ^ anchor for x in affine}
        if any(x ^ y not in translated for x in translated for y in translated):
            continue
        supports += 1
        for phase in phase_masks:
            negative = phase & support
            if negative >> anchor & 1:
                negative ^= support
            directions.add((support, negative))
    return dict(n=n, affine_supports=supports, directions=sorted(directions),
                tested_nonempty_subsets=(1 << points)-1, ambient_phases=len(phase_masks))


def vector(direction, n):
    support, negative = direction
    return tuple(0 if not support >> x & 1 else (-1 if negative >> x & 1 else 1)
                 for x in range(1 << n))


def pair_span_boolean_points(u, v):
    """Enumerate Boolean points in a rank-two real span using two coordinates."""
    pair = next(((i, j, u[i]*v[j]-u[j]*v[i]) for i in range(len(u)) for j in range(i+1, len(u))
                 if u[i]*v[j] != u[j]*v[i]), None)
    if pair is None:
        raise ValueError('expected independent directions')
    i, j, determinant = pair
    answer = set()
    for a in (0, 1):
        for b in (0, 1):
            first, second = a*v[j]-b*v[i], u[i]*b-u[j]*a
            values = [first*x+second*y for x, y in zip(u, v)]
            if all(x in (0, determinant) for x in values):
                answer.add(sum(1 << k for k, x in enumerate(values) if x == determinant))
    return answer


def small_two_piece_coverage(n):
    if not 0 <= n <= 3:
        raise ValueError('pair-span enumeration cap')
    data = enumerate_directions(n)
    directions = data['directions']
    vectors = [vector(d, n) for d in directions]
    single = {0} | {support for support, negative in directions if negative == 0}
    covered = set(single)
    peak = pairs = 0
    for first, second in combinations(vectors, 2):
        vertices = pair_span_boolean_points(first, second)
        assert len(vertices) <= 4
        peak = max(peak, len(vertices)); pairs += 1
        covered |= vertices
    return dict(n=n, directions=len(directions), one_piece_boolean_functions=len(single),
                two_piece_boolean_functions=len(covered), total_boolean_functions=1 << (1 << n),
                independent_pair_spans=pairs, max_boolean_points_in_pair_span=peak)
