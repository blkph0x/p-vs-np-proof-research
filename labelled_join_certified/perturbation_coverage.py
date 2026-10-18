"""Exact counting bounds for the same-coordinate B+UV representation."""
from hashlib import sha256


def _natural(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a nonnegative integer")
    return value


def graph_column_choices(r):
    """Zero, unit, or two-support column masks on r displayed rows."""
    r = _natural(r, "r")
    return 1 + r + r * (r - 1) // 2


def representation_upper_bound(n, r, p):
    """Number of B,U,V descriptions, hence an upper bound on row spaces."""
    n, r, p = (_natural(n, "n"), _natural(r, "r"), _natural(p, "p"))
    if r > n:
        raise ValueError("r cannot exceed n")
    return graph_column_choices(r) ** n * (1 << (p * (r + n)))


def all_row_count_upper_bound(n, p):
    """Upper bound after allowing any displayed row count from 0 through n."""
    n, p = _natural(n, "n"), _natural(p, "p")
    return sum(representation_upper_bound(n, rows, p) for rows in range(n + 1))


def systematic_rowspace_lower_bound(n, r):
    """Distinct row spaces of [I_r | M], for all binary M."""
    n, r = _natural(n, "n"), _natural(r, "r")
    if r > n:
        raise ValueError("r cannot exceed n")
    return 1 << (r * (n - r))


def excludes_universal_coverage(n, r, p):
    """Fixed displayed-row count version of the comparison."""
    return systematic_rowspace_lower_bound(n, r) > representation_upper_bound(n, r, p)


def excludes_universal_coverage_any_row_count(n, p, rank=None):
    """Compare rank ``rank`` spaces against every representation with <=n rows."""
    n, p = _natural(n, "n"), _natural(p, "p")
    rank = n // 2 if rank is None else _natural(rank, "rank")
    if rank > n:
        raise ValueError("rank cannot exceed n")
    return systematic_rowspace_lower_bound(n, rank) > all_row_count_upper_bound(n, p)


def largest_excluded_label_budget(n):
    """Largest p whose all-row-count description bound is still too small."""
    n = _natural(n, "n")
    lower = systematic_rowspace_lower_bound(n, n // 2)
    p = 0
    while all_row_count_upper_bound(n, p) < lower:
        p += 1
    return p - 1


def bound_record(n, r, p):
    upper = representation_upper_bound(n, r, p)
    lower = systematic_rowspace_lower_bound(n, r)
    all_upper = all_row_count_upper_bound(n, p)
    all_lower = systematic_rowspace_lower_bound(n, n // 2)
    def digest(value):
        data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), 'big')
        return sha256(data).hexdigest()
    return {"n": n, "r": r, "p": p,
            "representation_upper_bound_bit_length": upper.bit_length(),
            "representation_upper_bound_sha256": digest(upper),
            "systematic_rowspace_lower_bound_bit_length": lower.bit_length(),
            "systematic_rowspace_lower_bound_sha256": digest(lower),
            "universal_coverage_excluded": lower > upper,
            "all_row_count_upper_bound_bit_length": all_upper.bit_length(),
            "all_row_count_upper_bound_sha256": digest(all_upper),
            "all_row_count_systematic_lower_bound_bit_length": all_lower.bit_length(),
            "all_row_count_systematic_lower_bound_sha256": digest(all_lower),
            "universal_coverage_excluded_with_any_row_count": all_lower > all_upper,
            "largest_excluded_label_budget": largest_excluded_label_budget(n)}
