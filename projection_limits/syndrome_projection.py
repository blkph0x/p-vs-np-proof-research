"""Constructive limits of replacing binary parity checks by low-rank hashes.

The dependency builder is polynomial; exhaustive enumeration is restricted to
the independently checked, fixed 24-coordinate Golay control in run_golay_audit.
No result here rules out retaining or restoring additional original constraints.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import random
import sys
from time import perf_counter


def _rows(rows, width, name):
    if type(width) is not int or width < 0:
        raise ValueError("matrix width must be a nonnegative integer")
    try:
        result = tuple(rows)
    except TypeError as exc:
        raise ValueError(f"{name} must be iterable") from exc
    if any(type(row) is not int or row < 0 or row.bit_length() > width for row in result):
        raise ValueError(f"{name} must contain nonnegative binary vectors of the specified width")
    return result


def rank(rows, stats=None):
    basis = {}
    for row in rows:
        if stats is not None:
            stats["rank_rows"] += 1
        while row:
            if stats is not None:
                stats["rank_steps"] += 1
            pivot = row.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = row
                break
            row ^= basis[pivot]
    return len(basis)


def syndrome(rows, word):
    return sum(((row & word).bit_count() & 1) << i for i, row in enumerate(rows))


def project_rows(H_rows, Q_rows, n):
    H = _rows(H_rows, n, "H rows")
    Q = _rows(Q_rows, len(H), "Q rows")
    projected = []
    for combination in Q:
        value = 0
        while combination:
            bit = combination & -combination
            value ^= H[bit.bit_length() - 1]
            combination ^= bit
        projected.append(value)
    return tuple(projected)


def dependency_witness(rows, n):
    """Find a nonzero dependency among the first rank(rows)+1 columns.

    Return NO_NONZERO_KERNEL when n==rank(rows), where no such word exists.
    The number of supplied rows may exceed the actual rank. Elimination keeps
    original coordinate masks; zero columns correctly produce weight-one words.
    """
    rows = _rows(rows, n, "matrix rows")
    stats = {"rank_rows": 0, "rank_steps": 0, "prefix_bit_checks": 0,
             "column_steps": 0, "column_xors": 0}
    q = rank(rows, stats)
    if n <= q:
        return {"status": "NO_NONZERO_KERNEL", "rank": q, "row_count": len(rows),
                "word": None, "weight": None, "prefix_length": 0, "stats": stats}
    prefix = q + 1
    basis = {}
    for j in range(prefix):
        column = 0
        for i, row in enumerate(rows):
            stats["prefix_bit_checks"] += 1
            column |= ((row >> j) & 1) << i
        support = 1 << j
        while column:
            stats["column_steps"] += 1
            pivot = column.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = column, support
                break
            reduced, combination = basis[pivot]
            column ^= reduced
            support ^= combination
            stats["column_xors"] += 1
        if column == 0:
            if not support or syndrome(rows, support) or support.bit_count() > q + 1:
                raise ArithmeticError("dependency reconstruction invariant failed")
            return {"status": "WITNESS", "rank": q, "row_count": len(rows),
                    "word": support, "weight": support.bit_count(),
                    "prefix_length": prefix, "columns_processed": j + 1, "stats": stats}
    raise ArithmeticError("rank plus one columns unexpectedly independent")


def make_projection_witness(H_rows, Q_rows, n):
    H = _rows(H_rows, n, "H rows")
    Q = _rows(Q_rows, len(H), "Q rows")
    projected = project_rows(H, Q, n)
    result = dependency_witness(projected, n)
    result.update(n=n, original_rank=rank(H), projector_rank=rank(Q),
                  projected_rows=list(projected), projector_row_count=len(Q))
    if result["word"] is not None:
        result["original_syndrome"] = syndrome(H, result["word"])
        result["projected_syndrome"] = syndrome(projected, result["word"])
        result["spurious_for_original"] = bool(result["original_syndrome"])
    return result


def verify_projection_witness(H_rows, Q_rows, n, certificate):
    """Check supplied ranks, projection equality and explicit dependency support.

    This verifies a witness, not an original minimum-distance lower bound.
    The universal strict-distance conclusion additionally needs d > q+1.
    """
    try:
        H = _rows(H_rows, n, "H rows")
        Q = _rows(Q_rows, len(H), "Q rows")
        if type(certificate) is not dict or certificate.get("status") != "WITNESS":
            raise ValueError("a nonzero dependency witness is required")
        projected = project_rows(H, Q, n)
        q = rank(projected)
        for key, value in (("n", n), ("rank", q), ("row_count", len(Q)),
                           ("original_rank", rank(H)), ("projector_rank", rank(Q)),
                           ("projector_row_count", len(Q)), ("prefix_length", q + 1)):
            if type(certificate.get(key)) is not int or certificate[key] != value:
                raise ValueError("rank, dimension or prefix claim is incorrect")
        if n <= q or certificate.get("projected_rows") != list(projected):
            raise ValueError("projection or n>rank condition is incorrect")
        word = certificate["word"]
        if type(word) is not int or word <= 0 or word.bit_length() > q + 1:
            raise ValueError("nonzero word is not supported in the first q+1 coordinates")
        if type(certificate.get("weight")) is not int or certificate["weight"] != word.bit_count():
            raise ValueError("wrong witness weight")
        projected_syndrome, original_syndrome = syndrome(projected, word), syndrome(H, word)
        if projected_syndrome:
            raise ValueError("word violates a projected parity check")
        for key, value in (("projected_syndrome", projected_syndrome), ("original_syndrome", original_syndrome)):
            if type(certificate.get(key)) is not int or certificate[key] != value:
                raise ValueError("incorrect syndrome claim")
        if type(certificate.get("spurious_for_original")) is not bool or certificate["spurious_for_original"] != bool(original_syndrome):
            raise ValueError("incorrect spurious-witness claim")
        return {"valid": True, "rank": q, "weight": word.bit_count(),
                "spurious_for_original": bool(original_syndrome)}
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return {"valid": False, "reason": str(exc)}


def run_golay_audit():
    """Run twenty seeded projectors and save only a compact local result file."""
    started = perf_counter()
    directory = Path(__file__).resolve().parent
    previous = directory.parent
    sys.path.insert(0, str(previous))
    try:
        from all_dual_lp_barrier import golay_all_dual_certificate, verify_golay_certificate
    finally:
        sys.path.pop(0)
    reference = golay_all_dual_certificate()
    original_check = verify_golay_certificate(reference)
    if not original_check["verified"] or original_check["distance"] != 8:
        raise ArithmeticError("existing Golay distance certificate did not verify")
    H = tuple(reference["parity_check_rows"])
    if rank(H) != 12 or any(syndrome(H, row) for row in H):
        raise ArithmeticError("Golay row space is not self-dual of dimension twelve")
    span = {0}
    for row in H:
        span |= {word ^ row for word in tuple(span)}
    histogram = {}
    for word in span:
        histogram[word.bit_count()] = histogram.get(word.bit_count(), 0) + 1
    if len(span) != 4096 or min(word.bit_count() for word in span if word) != 8:
        raise ArithmeticError("independent complete codeword audit failed")
    rng = random.Random(20261018)
    cases = []
    for index in range(20):
        requested_rank = index % 7
        Q = []
        attempts = 0
        while len(Q) < requested_rank and attempts < 10000:
            candidate = rng.randrange(1 << 12)
            attempts += 1
            if rank(Q + [candidate]) > len(Q):
                Q.append(candidate)
        if len(Q) != requested_rank:
            raise ArithmeticError("finite projector generation attempt limit reached")
        independent = tuple(Q)
        # Extra rows deliberately exceed rank; they do not change the result.
        for _ in range(8):
            combination = rng.randrange(1 << requested_rank)
            row = 0
            for bit, value in enumerate(independent):
                if combination >> bit & 1:
                    row ^= value
            Q.append(row)
        rng.shuffle(Q)
        certificate = make_projection_witness(H, Q, 24)
        checked = verify_projection_witness(H, Q, 24, certificate)
        if not checked["valid"] or certificate["rank"] != requested_rank or not checked["spurious_for_original"]:
            raise ArithmeticError("seeded projection witness failed")
        cases.append({"index": index, "requested_rank": requested_rank, "Q_rows": Q,
                      "generation_attempts": attempts, "certificate": certificate,
                      "verified": True, "distance_strictly_reduced": certificate["rank"] + 1 < 8,
                      "projected_distance_upper_bound": certificate["weight"]})
    reference_paths = [previous / "all_dual_lp_barrier.py", previous / "ALL_DUAL_LP_THEOREM.md",
                       previous / "PROJECTION_RESULTS.json"]
    result = {"schema": "syndrome_rank_projection_limit_v1", "seed": 20261018,
              "n": 24, "H_rows": list(H), "original_rank": 12,
              "original_distance": 8, "codewords_verified": len(span),
              "self_duality_verified": True, "weight_distribution": dict(sorted(histogram.items())),
              "existing_distance_verifier_passed": True,
              "references": [{"path": "../" + path.name,
                              "sha256": sha256(path.read_bytes()).hexdigest()} for path in reference_paths],
              "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "test_source_sha256": sha256((directory / "test_syndrome_projection.py").read_bytes()).hexdigest(),
              "cases": cases, "elapsed_seconds": perf_counter() - started}
    (directory / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_golay_audit()
    print(f"Verified {len(result['cases'])} Golay projections; original distance {result['original_distance']}; "
          f"all projected witnesses have weight <=7 and violate original checks.")
