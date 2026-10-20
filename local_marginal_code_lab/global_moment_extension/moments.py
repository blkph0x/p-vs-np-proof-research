"""Exact finite controls for the explicitly defined L_k + Boolean M_1 hybrid.

No SDP solver, floating-point eigenvalue test, or optimization claim is used.
The closed formulas cost polynomially many bit operations in m.  Explicit
scope tables and dense matrices have separate, preflighted size limits.
"""

from fractions import Fraction


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def validate_dimensions(D, m):
    _integer(D, "D", 3)
    _integer(m, "m", D)
    if m > 4096:
        raise ValueError("explicit arithmetic guard: m <= 4096")


def gaussian_two(t):
    _integer(t, "t")
    return 0 if t < 2 else ((1 << t) - 1) * ((1 << t) - 2) // 6


def rank(columns):
    pivots = {}
    for column in columns:
        value = column
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def _scope(m, scope, maximum):
    _integer(maximum, "maximum")
    if type(scope) not in (list, tuple):
        raise ValueError("scope must be a list or tuple")
    if len(scope) > maximum:
        raise ValueError("explicit scope size limit")
    bound = 1 << m
    for point in scope:
        if type(point) is not int or not 0 < point < bound:
            raise ValueError("scope coordinates must be nonzero m-bit integers")
    if len(set(scope)) != len(scope):
        raise ValueError("scope coordinates must be distinct")
    return tuple(scope)


def parameters(D, m):
    validate_dimensions(D, m)
    Q, N = (1 << D) - 1, (1 << m) - 1
    a = (1 << (D - 2)) - 1
    p = Fraction(gaussian_two(D - 1), gaussian_two(D))
    q = Fraction(gaussian_two(D - 2), gaussian_two(D))
    r = Fraction(gaussian_two(D - 3), gaussian_two(D))
    beta = Fraction(a * (N - Q), N * (Q - 1) * (Q - a))
    mixed_p = (1 - beta) * p + beta
    mixed_q = (1 - beta) * q + beta
    mixed_r = (1 - beta) * r + beta
    mean = N * mixed_p
    old_variance = N * p + N * (N - 1) * q - (N * p) ** 2
    variance = N * mixed_p + N * (N - 1) * mixed_q - mean ** 2
    coupling = 3 * mixed_q + (N - 3) * mixed_r - mean * mixed_q
    # At m=D this coupling is zero.  The D=3 genuine witness also has q=0.
    quartic_value = -coupling ** 2 / mixed_q if mixed_q else Fraction(0)
    return {
        "D": D, "m": m, "N": N, "Q": Q, "a": a,
        "p": p, "q": q, "r": r, "beta": beta,
        "mixed_p": mixed_p, "mixed_q": mixed_q, "mixed_r": mixed_r,
        "old_variance": old_variance, "mixed_variance": variance,
        "contrast": mixed_p - mixed_q,
        "positive_aggregate_eigenvalue": 1 + N * mixed_p ** 2,
        "reduced_objective": mean, "total_objective": mean + 1,
        "integer_objective": 1 << (m - 2),
        "additive_gap": (1 << (m - 2)) - mean - 1,
        "degree_four_coupling": coupling,
        "degree_four_square_value": quartic_value,
    }


def moment(D, m, points, *, repaired=True):
    data = parameters(D, m)
    scope = _scope(m, tuple(points), 4096)
    dimension = rank(scope)
    numerator = gaussian_two(D - dimension) if dimension <= D else 0
    old = Fraction(numerator, gaussian_two(D))
    if type(repaired) is not bool:
        raise ValueError("repaired must be Boolean")
    return (1 - data["beta"]) * old + data["beta"] if repaired else old


def scope_table(D, m, scope, *, repaired=True, max_points=12):
    validate_dimensions(D, m)
    scope = _scope(m, scope, max_points)
    if type(repaired) is not bool:
        raise ValueError("repaired must be Boolean")
    data = parameters(D, m)
    denominator = gaussian_two(D)
    size = 1 << len(scope)
    values = []
    for mask in range(size):
        dimension = rank(scope[i] for i in range(len(scope)) if mask >> i & 1)
        values.append(Fraction(
            gaussian_two(D - dimension) if dimension <= D else 0,
            denominator))
    for bit in range(len(scope)):
        for mask in range(size):
            if not mask >> bit & 1:
                values[mask] -= values[mask | (1 << bit)]
    if repaired:
        values = [(1 - data["beta"]) * value for value in values]
        values[-1] += data["beta"]
    return values


def dense_moment_matrix(D, m, *, repaired=True, max_points=63):
    validate_dimensions(D, m)
    _integer(max_points, "max_points")
    if type(repaired) is not bool:
        raise ValueError("repaired must be Boolean")
    N = (1 << m) - 1
    if N > max_points:
        raise ValueError("dense matrix size limit")
    data = parameters(D, m)
    p = data["mixed_p" if repaired else "p"]
    q = data["mixed_q" if repaired else "q"]
    return [
        [Fraction(1)] + [p] * N,
        *[[p] + [p if i == j else q for j in range(N)] for i in range(N)],
    ]


def json_value(value):
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value
