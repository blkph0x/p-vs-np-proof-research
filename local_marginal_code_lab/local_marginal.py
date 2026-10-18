"""Exact local-marginal relaxation controls for pinned binary linear codes.

The relaxation stores one distribution for each coordinate scope of size at
most k, requires exact marginal consistency, and forbids assignments that do
not occur in the pinned code projection.  It is deliberately named here
instead of being identified with a particular lifted hierarchy.
"""

from __future__ import annotations

from math import comb


def validate_rows(rows, n):
    if type(n) is not int or n < 0:
        raise ValueError("nonnegative length required")
    rows = tuple(rows)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in rows):
        raise ValueError("rows must be n-bit integers")
    return rows


def basis(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return tuple(pivots[bit] for bit in sorted(pivots, reverse=True))


def span(rows, limit=1 << 20):
    rows = basis(rows)
    if len(rows) >= 0 and (1 << len(rows)) > limit:
        return None
    words = [0]
    for row in rows:
        words += [word ^ row for word in tuple(words)]
    return tuple(sorted(words))


def orthogonal_basis(rows, n):
    reduced = list(rows)
    pivots = []
    rank = 0
    for bit in range(n):
        index = next((i for i in range(rank, len(reduced))
                      if reduced[i] >> bit & 1), None)
        if index is None:
            continue
        reduced[rank], reduced[index] = reduced[index], reduced[rank]
        for i in range(len(reduced)):
            if i != rank and reduced[i] >> bit & 1:
                reduced[i] ^= reduced[rank]
        pivots.append(bit)
        rank += 1
    result = []
    for free in range(n):
        if free in pivots:
            continue
        word = 1 << free
        for index, pivot in enumerate(pivots):
            if reduced[index] >> free & 1:
                word |= 1 << pivot
        result.append(word)
    return tuple(result)


def project(word, scope):
    return tuple((word >> coordinate) & 1 for coordinate in scope)


def scope_count(n, k):
    return sum(comb(n, size) for size in range(k + 1))


def atom_slot_count(n, k):
    return sum(comb(n, size) * (1 << size) for size in range(k + 1))


def random_code_union_bound(n):
    """Exact bad-event bound for a random (n/2)-by-n generator matrix."""
    if type(n) is not int or n < 32 or n % 16:
        raise ValueError("n must be a multiple of 16 and at least 32")
    rank_value = n // 2
    distance = n // 16
    ball = sum(comb(n, weight) for weight in range(distance))
    denominator = 1 << rank_value
    numerator = 2 * ball
    return {
        "n": n,
        "rank": rank_value,
        "distance_lower_bound": distance,
        "local_level_lower_bound": distance - 2,
        "low_weight_ball": ball,
        "bad_probability_numerator": numerator,
        "bad_probability_denominator": denominator,
        "good_probability_lower_numerator": denominator - numerator,
        "strictly_positive_good_probability": denominator > numerator,
        "atom_slots_at_level": atom_slot_count(n, distance - 2),
    }


def local_point_is_supported(codewords, n, pin, k):
    """Check the deterministic e_pin point on every scope up to k."""
    target = 1 << pin
    checked = 0
    for mask in range(1 << n):
        if mask.bit_count() > k:
            continue
        scope = tuple(i for i in range(n) if mask >> i & 1)
        desired = project(target, scope)
        if not any(project(word, scope) == desired and word >> pin & 1
                   for word in codewords):
            return False, checked, scope
        checked += 1
    return True, checked, None


def make_certificate(rows, n, pin, k, *, enumerate_scopes=True, word_limit=1 << 20):
    rows = validate_rows(rows, n)
    if type(pin) is not int or not 0 <= pin < n:
        raise ValueError("pin out of range")
    if type(k) is not int or k < 0 or k > n:
        raise ValueError("invalid level")
    codewords = span(rows, word_limit)
    if codewords is None:
        return {"status": "UNKNOWN", "reason": "CODE_WORD_LIMIT"}
    dual_basis = orthogonal_basis(rows, n)
    dual_words = span(dual_basis, word_limit)
    if dual_words is None:
        return {"status": "UNKNOWN", "reason": "DUAL_WORD_LIMIT"}
    dual_distance = min((word.bit_count() for word in dual_words if word), default=None)
    pinned = tuple(word for word in codewords if word >> pin & 1)
    if not pinned:
        raise ValueError("pin is infeasible")
    pinned_distance = min(word.bit_count() for word in pinned)
    supported = None
    checked_scopes = None
    counterexample = None
    if enumerate_scopes:
        supported, checked_scopes, counterexample = local_point_is_supported(
            codewords, n, pin, k)
    # A scope omitting the pin is still conditioned through that omitted
    # coordinate, so both scope types are guaranteed only through delta - 2.
    theorem_bound = None if dual_distance is None else dual_distance - 2
    certificate = {
        "schema": "local_pinned_marginal_v1",
        "n": n,
        "generator_rows": list(rows),
        "dual_basis": list(dual_basis),
        "code_dimension": len(basis(rows)),
        "dual_distance": dual_distance,
        "pin": pin,
        "level": k,
        "theorem_level_bound": theorem_bound,
        "pinned_integer_optimum": pinned_distance,
        "relaxation_point_weight": 1,
        "scope_count": scope_count(n, k),
        "atom_slot_count": atom_slot_count(n, k),
        "enumerated_support": supported,
        "checked_scopes": checked_scopes,
        "support_counterexample": None if counterexample is None else list(counterexample),
    }
    return {"status": "FOUND", "certificate": certificate}


def verify_certificate(certificate, *, word_limit=1 << 20):
    try:
        if not isinstance(certificate, dict) or certificate.get("schema") != "local_pinned_marginal_v1":
            raise ValueError("invalid schema")
        n = certificate["n"]
        rows = validate_rows(certificate["generator_rows"], n)
        pin, k = certificate["pin"], certificate["level"]
        if type(pin) is not int or not 0 <= pin < n:
            raise ValueError("invalid pin")
        if type(k) is not int or not 0 <= k <= n:
            raise ValueError("invalid level")
        codewords = span(rows, word_limit)
        dual_basis = orthogonal_basis(rows, n)
        dual_words = span(dual_basis, word_limit)
        if codewords is None or dual_words is None:
            return {"status": "UNKNOWN", "valid": False, "reason": "WORD_LIMIT"}
        if tuple(certificate["dual_basis"]) != dual_basis:
            raise ValueError("dual basis mismatch")
        dual_distance = min((word.bit_count() for word in dual_words if word), default=None)
        if certificate["dual_distance"] != dual_distance:
            raise ValueError("dual distance mismatch")
        pinned = tuple(word for word in codewords if word >> pin & 1)
        if not pinned:
            raise ValueError("pinned code is empty")
        pinned_distance = min(word.bit_count() for word in pinned)
        if certificate["pinned_integer_optimum"] != pinned_distance:
            raise ValueError("pinned optimum mismatch")
        if certificate["relaxation_point_weight"] != 1:
            raise ValueError("unit point weight must be one")
        theorem_bound = None if dual_distance is None else dual_distance - 2
        if certificate["theorem_level_bound"] != theorem_bound:
            raise ValueError("theorem bound mismatch")
        theorem_valid = theorem_bound is not None and k <= theorem_bound
        if certificate["scope_count"] != scope_count(n, k):
            raise ValueError("scope count mismatch")
        if certificate["atom_slot_count"] != atom_slot_count(n, k):
            raise ValueError("atom count mismatch")
        supported, checked, counterexample = local_point_is_supported(codewords, n, pin, k)
        if certificate["enumerated_support"] is not None and certificate["enumerated_support"] != supported:
            raise ValueError("support replay mismatch")
        if certificate["checked_scopes"] is not None and certificate["checked_scopes"] != checked:
            raise ValueError("scope replay mismatch")
        return {
            "status": "VERIFIED",
            "valid": True,
            "theorem_level_valid": theorem_valid,
            "support_replay": supported,
            "checked_scopes": checked,
            "dual_distance": dual_distance,
            "pinned_integer_optimum": pinned_distance,
            "relaxation_point_weight": 1,
            "integrality_gap": pinned_distance,
            "counterexample": None if counterexample is None else list(counterexample),
        }
    except (KeyError, TypeError, ValueError):
        return {"status": "INVALID", "valid": False}
