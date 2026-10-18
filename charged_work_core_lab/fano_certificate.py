"""Bounded F7-minor discovery with a separate, polynomial rank verifier.

Columns are nonnegative integer bit vectors over GF(2). A successful certificate
rules out graphic and cographic matroids; a failed search proves nothing.
"""
from __future__ import annotations

from itertools import combinations
import random
from typing import Sequence


SCHEMA = "binary_fano_minor_v1"


def _columns(values: Sequence[int]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes, dict)):
        raise ValueError("columns must be a sequence of nonnegative integers")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise ValueError("columns must be an iterable") from exc
    if any(type(value) is not int or value < 0 for value in result):
        raise ValueError("columns must contain only nonnegative integers")
    return result


def _rank_for_verification(vectors: Sequence[int]) -> int:
    """Row elimination, intentionally separate from the search's reducer."""
    rows = list(vectors)
    rank = 0
    for bit in range(max(rows, default=0).bit_length() - 1, -1, -1):
        pivot = next((j for j in range(rank, len(rows)) if rows[j] & (1 << bit)), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for j in range(rank + 1, len(rows)):
            if rows[j] & (1 << bit):
                rows[j] ^= rows[rank]
        rank += 1
    return rank


def verify_fano_certificate(columns: Sequence[int], certificate: object) -> dict:
    """Check an F7 minor from original coordinates; malformed input is invalid.

    No search projection is trusted. Rank identities separately prove a simple
    rank-three seven-element quotient, and then check its explicit labels.
    All unlisted coordinates are deleted after the listed contraction.
    """
    errors = []
    try:
        cols = _columns(columns)
    except ValueError as exc:
        return {"valid": False, "errors": [str(exc)]}
    if not isinstance(certificate, dict):
        return {"valid": False, "errors": ["certificate must be a dictionary"]}
    if certificate.get("schema") != SCHEMA:
        errors.append("unrecognized certificate schema")
    n = len(cols)
    matroid_rank = _rank_for_verification(cols)
    for name, expected in (("n", n), ("matroid_rank", matroid_rank)):
        if type(certificate.get(name)) is not int or certificate[name] != expected:
            errors.append(f"{name} does not match the supplied columns")
    indices = {}
    for name, length in (("contraction_indices", None), ("retained_indices", 7),
                         ("quotient_basis_indices", 3)):
        values = certificate.get(name)
        if not isinstance(values, (list, tuple)):
            errors.append(f"{name} must be a list of indices")
            continue
        if any(type(j) is not int or not 0 <= j < n for j in values):
            errors.append(f"{name} contains an invalid or out-of-range index")
            continue
        if len(set(values)) != len(values):
            errors.append(f"{name} contains duplicate indices")
        if length is not None and len(values) != length:
            errors.append(f"{name} must contain exactly {length} indices")
        indices[name] = list(values)
    labels = certificate.get("quotient_vectors")
    if not isinstance(labels, (list, tuple)) or len(labels) != 7:
        errors.append("quotient_vectors must contain seven integer labels")
    elif any(type(x) is not int or not 1 <= x <= 7 for x in labels):
        errors.append("quotient_vectors labels must be integers in 1..7")
    elif len(set(labels)) != 7:
        errors.append("quotient_vectors must contain all seven nonzero labels")
    if errors:
        return {"valid": False, "errors": errors}
    contracted = indices["contraction_indices"]
    retained = indices["retained_indices"]
    basis_ids = indices["quotient_basis_indices"]
    if set(contracted) & set(retained):
        errors.append("contraction and retention overlap")
    if not set(basis_ids) <= set(retained):
        errors.append("quotient basis must be selected from retained indices")
    base = [cols[j] for j in contracted]
    base_rank = _rank_for_verification(base)
    if base_rank != len(contracted):
        errors.append("contracted columns must be independent")
    quotient_rank = _rank_for_verification(base + [cols[j] for j in retained]) - base_rank
    if quotient_rank != 3:
        errors.append("retained columns do not have quotient rank three")
    for j in retained:
        if _rank_for_verification(base + [cols[j]]) != base_rank + 1:
            errors.append(f"retained coordinate {j} becomes a loop")
    for a, b in combinations(retained, 2):
        if _rank_for_verification(base + [cols[a], cols[b]]) != base_rank + 2:
            errors.append(f"retained coordinates {a},{b} are dependent in the quotient")
    if _rank_for_verification(base + [cols[j] for j in basis_ids]) != base_rank + 3:
        errors.append("quotient basis is not independent modulo the contraction")
    for j, label in zip(retained, labels):
        difference = cols[j]
        for bit, basis_id in enumerate(basis_ids):
            if label & (1 << bit):
                difference ^= cols[basis_id]
        if _rank_for_verification(base + [difference]) != base_rank:
            errors.append(f"quotient label for retained coordinate {j} is incorrect")
    return {"valid": not errors, "errors": errors, "n": n,
            "matroid_rank": matroid_rank, "contraction_rank": base_rank,
            "retained_quotient_rank": quotient_rank,
            "verified_quotient_vectors": list(labels) if not errors else None,
            "minor": "F7" if not errors else None,
            "neither_graphic_nor_cographic": not errors}


def find_fano_minor(columns: Sequence[int], *, max_trials: int = 256,
                    seed: int = 8128) -> dict:
    """Try deterministically seeded bases; return FOUND or UNKNOWN.

    Each trial contracts rank(M)-3 independent columns. This restricted bounded
    search is not a complete F7-minor recognition algorithm. Search counters
    measure reductions and integer XORs; timings belong in the caller.
    """
    cols = _columns(columns)
    if type(max_trials) is not int or max_trials < 0:
        raise ValueError("max_trials must be a nonnegative integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    stats = {"seed": seed, "max_trials": max_trials, "trials": 0,
             "vector_reductions": 0, "xor_operations": 0}

    def reduce_vector(value, basis):
        stats["vector_reductions"] += 1
        for pivot in sorted(basis, reverse=True):
            if value & (1 << pivot):
                value ^= basis[pivot]
                stats["xor_operations"] += 1
        return value

    full_basis = {}
    for col in cols:
        reduced = reduce_vector(col, full_basis)
        if reduced:
            full_basis[reduced.bit_length() - 1] = reduced
    rank = len(full_basis)
    unknown = {"status": "UNKNOWN", "certificate": None, "search": stats}
    if rank < 3 or len(cols) < rank + 4:
        unknown["reason"] = "input too small for this rank-three quotient search"
        return unknown
    rng = random.Random(seed)
    for trial in range(max_trials):
        stats["trials"] = trial + 1
        order = list(range(len(cols)))
        rng.shuffle(order)
        contracted = []
        basis = {}
        for j in order:
            if len(contracted) == rank - 3:
                break
            reduced = reduce_vector(cols[j], basis)
            if reduced:
                basis[reduced.bit_length() - 1] = reduced
                contracted.append(j)
        representatives = {}
        for j, col in enumerate(cols):
            reduced = reduce_vector(col, basis)
            if reduced:
                representatives.setdefault(reduced, j)
        if len(representatives) != 7:
            continue
        retained = list(representatives.values())
        quotient_basis = {}
        basis_ids = []
        basis_values = []
        for quotient, j in representatives.items():
            reduced = reduce_vector(quotient, quotient_basis)
            if reduced:
                quotient_basis[reduced.bit_length() - 1] = reduced
                basis_ids.append(j)
                basis_values.append(quotient)
        labels_by_value = {}
        for label in range(1, 8):
            value = 0
            for bit, vector in enumerate(basis_values):
                if label & (1 << bit):
                    value ^= vector
                    stats["xor_operations"] += 1
            labels_by_value[value] = label
        certificate = {"schema": SCHEMA, "n": len(cols), "matroid_rank": rank,
                       "contraction_indices": contracted, "retained_indices": retained,
                       "quotient_basis_indices": basis_ids,
                       "quotient_vectors": [labels_by_value[value] for value in representatives]}
        check = verify_fano_certificate(cols, certificate)
        if not check["valid"]:
            raise AssertionError(f"search produced an invalid certificate: {check['errors']}")
        return {"status": "FOUND", "certificate": certificate, "search": stats}
    unknown["reason"] = "bounded search exhausted; no nonexistence claim"
    return unknown
