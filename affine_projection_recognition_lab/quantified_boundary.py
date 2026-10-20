"""Finite checks of the written variable-width Pi_2^P reduction.

This is an exhaustive experiment, not an efficient QBF solver. Integer masks
use little-endian variable order. Source variables are u followed by v; the
constructed CNF uses a,b,u,v. All complete assignments are evaluated, including
after finding a witness, to make the formula-evaluation counter literal.
"""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path

SCHEMA = "quantified-affine-boundary-v1"
DEFAULT_MAX_EVALUATIONS = 20480


def source(p, q, clauses):
    """Validate explicit partition sizes and DIMACS literals without coercion."""
    if type(p) is not int or type(q) is not int or p < 0 or q < 0:
        raise ValueError("partition sizes must be nonnegative integers")
    if not isinstance(clauses, (list, tuple)):
        raise ValueError("clauses must be a sequence")
    normalized = []
    for clause in clauses:
        if not isinstance(clause, (list, tuple)):
            raise ValueError("each clause must be a sequence")
        if any(type(lit) is not int or lit == 0 or abs(lit) > p + q for lit in clause):
            raise ValueError("source literal outside the explicit partition")
        normalized.append(list(clause))
    return {"universal_width": p, "existential_width": q, "clauses": normalized}


def lift(spec):
    """Return the guarded CNF; this construction performs no truth-table search."""
    checked = source(spec["universal_width"], spec["existential_width"], spec["clauses"])
    return [[-1, -2] + [lit + 2 if lit > 0 else lit - 2 for lit in row]
            for row in checked["clauses"]]


def evaluate(clauses, mask):
    return all(any(bool(mask & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause) for clause in clauses)


def affine_by_rank(points):
    """An affine set equals its affine hull iff its size equals 2^rank."""
    if not points:
        return False
    base = points[0]
    pivots = {}
    for point in points:
        value = point ^ base
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(points) == 1 << len(pivots)


def record(spec, max_evaluations=DEFAULT_MAX_EVALUATIONS):
    spec = source(spec["universal_width"], spec["existential_width"], spec["clauses"])
    if type(max_evaluations) is not int or max_evaluations < 0:
        raise ValueError("max_evaluations must be a nonnegative integer")
    p, q = spec["universal_width"], spec["existential_width"]
    # Test 5*2^(p+q) <= cap without first allocating a potentially huge integer.
    if (max_evaluations // 5).bit_length() <= p + q:
        return {"status": "UNKNOWN_CAP", "source": spec,
                "max_formula_evaluations": max_evaluations}
    clauses = spec["clauses"]
    lifted = lift(spec)
    row_counts = []
    evaluations = 0
    for u in range(1 << p):
        count = 0
        for v in range(1 << q):
            count += evaluate(clauses, u | (v << p))
            evaluations += 1
        row_counts.append(count)
    bits = []
    for x in range(1 << (p + 2)):
        count = 0
        for v in range(1 << q):
            count += evaluate(lifted, x | (v << (p + 2)))
            evaluations += 1
        bits.append(int(count > 0))
    good = all(row_counts)
    points = [x for x, bit in enumerate(bits) if bit]
    affine = affine_by_rank(points)
    if affine != good:
        raise AssertionError("quantified reduction failed")
    violation = None
    if not good:
        u = row_counts.index(0)
        parents = [u << 2, (u << 2) | 1, (u << 2) | 2]
        missing = parents[0] ^ parents[1] ^ parents[2]
        if not all(bits[x] for x in parents) or bits[missing]:
            raise AssertionError("invalid ternary-closure counterexample")
        violation = {"universal_mask": u, "parents": parents, "missing": missing}
    return {"status": "EXACT", "source": spec, "lifted_clauses": lifted,
            "source_witness_counts": row_counts, "qbf_true": bool(good),
            "projection_bits": bits, "projection_affine": affine,
            "ternary_violation": violation, "formula_evaluations": evaluations}


def examples():
    return [
        source(0, 0, []), source(0, 0, [[]]),
        source(1, 1, [[-1, 2], [1, -2]]),  # v must equal u: true forall-exists
        source(1, 1, [[1]]),               # one universal fiber absent
        source(1, 1, [[2], [-2]]),
        source(2, 0, [[1, -1]]),           # tautology
        source(2, 0, [[1], [1]]),          # duplicate clause
        source(0, 2, [[1, 2], [-1, -2]]),
    ]


def campaign_sources():
    # Every subset of the nine non-tautological clauses (including empty) on
    # two variables, for each split into zero, one, or two universal variables.
    pool = [[(i + 1) * sign for i, sign in enumerate(signs) if sign]
            for signs in product((-1, 0, 1), repeat=2)]
    for p in range(3):
        for selection in range(1 << len(pool)):
            yield source(p, 2 - p,
                         [row for i, row in enumerate(pool) if selection & (1 << i)])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def build_artifact():
    digest = hashlib.sha256()
    totals = {"cases": 0, "true": 0, "false": 0, "formula_evaluations": 0}
    for spec in campaign_sources():
        result = record(spec)
        digest.update((canonical(result) + "\n").encode("ascii"))
        totals["cases"] += 1
        totals["true" if result["qbf_true"] else "false"] += 1
        totals["formula_evaluations"] += result["formula_evaluations"]
    return {"schema": SCHEMA, "status": "EXACT_FINITE_REDUCTION_CHECKS",
            "campaign": {**totals, "records_sha256": digest.hexdigest()},
            "examples": [record(spec) for spec in examples()],
            "scope": "Finite regression evidence; the all-input proof is in COMPLEXITY_THEOREM.md."}


if __name__ == "__main__":
    artifact = build_artifact()
    Path(__file__).with_name("QUANTIFIED_RESULTS.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(artifact["campaign"], sort_keys=True))
