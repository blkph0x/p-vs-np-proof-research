"""Exact operation counts for full Walsh-Hadamard and Boolean zeta passes."""
from __future__ import annotations


def _dimension(values):
    length = len(values)
    if length < 1 or length & (length - 1):
        raise ValueError("transform length must be a positive power of two")
    return length.bit_length() - 1


def counted_fwht(values):
    """Return the unnormalized FWHT and exact add/subtract counts."""
    dimension = _dimension(values)
    out = list(values)
    additions = subtractions = butterflies = 0
    step = 1
    while step < len(out):
        for base in range(0, len(out), 2 * step):
            for offset in range(step):
                left, right = out[base + offset], out[base + offset + step]
                out[base + offset] = left + right
                out[base + offset + step] = left - right
                additions += 1
                subtractions += 1
                butterflies += 1
        step *= 2
    expected = dimension * len(out) // 2
    assert butterflies == expected
    return out, {"dimension": dimension, "length": len(out),
                 "butterflies": butterflies, "additions": additions,
                 "subtractions": subtractions,
                 "arithmetic_operations": additions + subtractions}


def counted_subset_zeta(values):
    """Return the subset zeta transform and exact addition count."""
    dimension = _dimension(values)
    out = list(values)
    additions = 0
    for bit in range(dimension):
        mask = 1 << bit
        for subset in range(len(out)):
            if subset & mask:
                out[subset] += out[subset ^ mask]
                additions += 1
    expected = dimension * len(out) // 2
    assert additions == expected
    return out, {"dimension": dimension, "length": len(out),
                 "additions": additions}


def exact_cost(dimension):
    if type(dimension) is not int or dimension < 0:
        raise ValueError("dimension must be a nonnegative integer")
    length = 1 << dimension
    butterflies = dimension * length // 2
    fwht_additions = butterflies
    fwht_subtractions = butterflies
    zeta_additions = butterflies
    return {
        "dimension": dimension,
        "state_count": length,
        "fwht_butterflies": butterflies,
        "fwht_additions": fwht_additions,
        "fwht_subtractions": fwht_subtractions,
        "fwht_arithmetic_operations": fwht_additions + fwht_subtractions,
        "zeta_additions": zeta_additions,
        "combined_add_sub_operations": fwht_additions + fwht_subtractions + zeta_additions,
    }
