"""Exact binary-code minweight by conditioning coordinates and solving affine cosets.

The search is exponential in the number of fixed coordinates and residual trellis
width. Explicit work limits return UNKNOWN, never an optimality/hardness claim.
Only Python's standard library is needed. Coordinates are zero-based bit positions.
"""
from __future__ import annotations

from itertools import combinations
from time import perf_counter


def _nonnegative_int(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def validate_generator(generator, n):
    _nonnegative_int(n, "n")
    rows = tuple(generator)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in rows):
        raise ValueError("generator rows must be nonnegative n-bit integers")
    return rows


def row_basis(rows):
    """Echelon basis with descending pivots (also accepts column vectors)."""
    basis = {}
    for value in rows:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return tuple(basis[p] for p in sorted(basis, reverse=True))


def _in_span(basis, value):
    for vector in basis:
        if value & (1 << (vector.bit_length() - 1)):
            value ^= vector
    return value == 0


def parity_check(generator, n):
    """A basis of the orthogonal complement; dependent input rows are supported."""
    rows = list(validate_generator(generator, n))
    pivots = []
    rank = 0
    for column in range(n):
        hit = next((i for i in range(rank, len(rows)) if rows[i] >> column & 1), None)
        if hit is None:
            continue
        rows[rank], rows[hit] = rows[hit], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i] >> column & 1:
                rows[i] ^= rows[rank]
        pivots.append(column)
        rank += 1
    result = []
    for free in sorted(set(range(n)) - set(pivots)):
        word = 1 << free
        for row, pivot in zip(rows[:rank], pivots):
            if row >> free & 1:
                word |= 1 << pivot
        result.append(word)
    return tuple(result)


def columns_from_rows(rows, n):
    return tuple(sum(1 << i for i, row in enumerate(rows) if row >> j & 1) for j in range(n))


def _coordinates(values, n, name, full=False):
    values = tuple(values)
    if any(type(j) is not int or not 0 <= j < n for j in values):
        raise ValueError(f"{name} contains invalid coordinates")
    if len(set(values)) != len(values) or (full and len(values) != n):
        raise ValueError(f"{name} must contain distinct coordinates" + (" and cover all n coordinates" if full else ""))
    return values


def conditioned_width_profile(generator, n, deleted=(), order=None):
    """Fixed-order syndrome width of a nonempty conditioned coset, via GF(2) ranks.

    Conditioning means fixing the deleted bits, not freely puncturing them. All
    feasible fixed assignments give affine translates of the same shortened
    code and hence the same state-count profile (before the nonzero flag).
    """
    rows = validate_generator(generator, n)
    deleted = _coordinates(deleted, n, "deleted")
    order = _coordinates(range(n) if order is None else order, n, "order", full=True)
    columns = columns_from_rows(parity_check(rows, n), n)
    removed = set(deleted)
    remaining = tuple(j for j in order if j not in removed)
    return _profile_from_columns(columns, remaining)


def _profile_from_columns(columns, remaining):
    vectors = [columns[j] for j in remaining]
    rank_all = len(row_basis(vectors))
    profile = [len(row_basis(vectors[:i])) + len(row_basis(vectors[i:])) - rank_all
               for i in range(len(vectors) + 1)]
    return {"width": max(profile, default=0), "profile": profile,
            "peak_syndrome_states": 1 << max(profile, default=0),
            "rank_evaluations": 2 * (len(vectors) + 1) + 1,
            "remaining_order": list(remaining)}


def choose_deletion(generator, n, delete_count=1, order=None, max_candidates=10000):
    """Bounded exhaustive candidate selection for one *fixed* coordinate order.

    Scores use peak and total syndrome states, then coordinate indices. The result
    is not a globally optimal order/decomposition. Discovery costs are reported.
    """
    started = perf_counter()
    rows = validate_generator(generator, n)
    _nonnegative_int(delete_count, "delete_count")
    _nonnegative_int(max_candidates, "max_candidates")
    if delete_count > n:
        raise ValueError("delete_count exceeds n")
    order = _coordinates(range(n) if order is None else order, n, "order", full=True)
    columns = columns_from_rows(parity_check(rows, n), n)
    candidates = rank_calls = 0
    best = None
    complete = True
    for deleted in combinations(range(n), delete_count):
        if candidates == max_candidates:
            complete = False
            break
        removed = set(deleted)
        profile = _profile_from_columns(columns, tuple(j for j in order if j not in removed))
        candidates += 1
        rank_calls += profile["rank_evaluations"]
        score = (profile["width"], sum(1 << x for x in profile["profile"]), deleted)
        if best is None or score < best[0]:
            best = (score, deleted, profile)
    return {"status": "COMPLETE" if complete else "CANDIDATE_LIMIT",
            "deleted": list(best[1]) if best else None,
            "selected_profile": best[2] if best else None,
            "candidates_evaluated": candidates, "rank_evaluations": rank_calls,
            "seconds": perf_counter() - started}


def minimum_distance(generator, n, *, deleted=(), order=None,
                     max_transitions=1000000, max_branches=256):
    """Minimize nonzero weight exactly, or return UNKNOWN when a budget is used.

    Each assignment b on D is charged |b| and solves H_R x = H_D b. Trellis
    states track syndrome and whether the full word is nonzero. Feasible words
    reconstructed in completed branches remain upper bounds on interruption.
    The budgets cap branch assignments and DP transition attempts; polynomial
    input validation, Gaussian elimination and suffix-span setup are separate.
    """
    started = perf_counter()
    rows = validate_generator(generator, n)
    deleted = _coordinates(deleted, n, "deleted")
    order = _coordinates(range(n) if order is None else order, n, "order", full=True)
    _nonnegative_int(max_transitions, "max_transitions")
    _nonnegative_int(max_branches, "max_branches")
    checks = parity_check(rows, n)
    columns = columns_from_rows(checks, n)
    removed = set(deleted)
    remaining = tuple(j for j in order if j not in removed)
    suffix = [()] * (len(remaining) + 1)
    for i in range(len(remaining) - 1, -1, -1):
        suffix[i] = row_basis((*suffix[i + 1], columns[remaining[i]]))

    stats = {"n": n, "dimension": n - len(checks), "deleted": list(deleted),
             "remaining_order": list(remaining), "branch_assignments_total": 1 << len(deleted),
             "branches_completed": 0, "branches_feasible": 0, "transitions": 0,
             "peak_syndrome_states": 0, "peak_dp_entries": 0,
             "sum_layer_syndrome_states": 0,
             "max_transitions": max_transitions, "max_branches": max_branches}
    best_weight = best_word = None

    def result(status, reason=None):
        # Membership is rechecked against the ORIGINAL code, not a punctured code.
        if best_word is not None:
            if not best_word or best_word.bit_count() != best_weight or any(
                    (row & best_word).bit_count() % 2 for row in checks):
                raise ArithmeticError("reconstruction failed original-code membership check")
        return {**stats, "status": status, "reason": reason,
                "distance": best_weight if status == "EXACT" else None,
                "upper_bound": best_weight, "word": best_word,
                "seconds": perf_counter() - started}

    def record_layer(states):
        syndrome_count = len({key[0] for key in states})
        stats["peak_syndrome_states"] = max(stats["peak_syndrome_states"], syndrome_count)
        stats["peak_dp_entries"] = max(stats["peak_dp_entries"], len(states))
        stats["sum_layer_syndrome_states"] += syndrome_count

    for assignment in range(1 << len(deleted)):
        if stats["branches_completed"] == max_branches:
            return result("UNKNOWN", "BRANCH_LIMIT")
        target = fixed_word = 0
        for i, coordinate in enumerate(deleted):
            if assignment >> i & 1:
                target ^= columns[coordinate]
                fixed_word |= 1 << coordinate
        if not _in_span(suffix[0], target):
            stats["branches_completed"] += 1
            continue
        stats["branches_feasible"] += 1
        current = {(0, bool(fixed_word)): (fixed_word.bit_count(), fixed_word)}
        record_layer(current)
        for i, coordinate in enumerate(remaining):
            next_states = {}
            for (syndrome, used), (cost, word) in current.items():
                for bit in (0, 1):
                    if stats["transitions"] == max_transitions:
                        return result("UNKNOWN", "TRANSITION_LIMIT")
                    stats["transitions"] += 1
                    next_syndrome = syndrome ^ (columns[coordinate] if bit else 0)
                    if not _in_span(suffix[i + 1], target ^ next_syndrome):
                        continue
                    key = next_syndrome, used or bool(bit)
                    candidate = cost + bit, word | ((1 << coordinate) if bit else 0)
                    if key not in next_states or candidate < next_states[key]:
                        next_states[key] = candidate
            current = next_states
            record_layer(current)
        candidate = current.get((target, True))
        if candidate is not None and (best_weight is None or candidate < (best_weight, best_word)):
            best_weight, best_word = candidate
        stats["branches_completed"] += 1
    return result("EXACT")
