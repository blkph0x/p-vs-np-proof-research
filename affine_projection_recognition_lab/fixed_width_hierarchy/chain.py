"""Bounded exact controls for the fixed-width Boolean-hierarchy theorem.

This program explicitly enumerates relations and assignments. It is not the
polynomial reduction's claimed running time and is not an efficient SAT solver.
All variable indices in clauses are signed one-based DIMACS indices.
"""
from __future__ import annotations

import hashlib
import json
from itertools import product

MAX_WIDTH = 4
MAX_EXHAUSTIVE_VARIABLES = 18
SCHEMA = "fixed-width-affine-hierarchy-v1"
REDUCTION_SCHEMA = "fixed-width-affine-prefix-v1"


def width(value):
    if type(value) is not int or not 0 <= value <= MAX_WIDTH:
        raise ValueError("finite control requires an integer visible width from 0 to 4")
    return value


def source(spec):
    if not isinstance(spec, dict) or set(spec) != {"nvars", "clauses"}:
        raise ValueError("source needs exactly nvars and clauses")
    n = spec["nvars"]
    if type(n) is not int or not 0 <= n <= MAX_EXHAUSTIVE_VARIABLES:
        raise ValueError("source variable count exceeds the finite-control range")
    if not isinstance(spec["clauses"], (list, tuple)):
        raise ValueError("clauses must be a sequence")
    rows = []
    for row in spec["clauses"]:
        if not isinstance(row, (list, tuple)):
            raise ValueError("a clause must be a sequence")
        if any(type(lit) is not int or not lit or abs(lit) > n for lit in row):
            raise ValueError("literal outside its source variable block")
        rows.append(list(row))
    return {"nvars": n, "clauses": rows}


def source_digest(k, sources):
    payload = {"visible_width": k, "sources": sources}
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def affine_by_rank(relation, k):
    """Empty is rejected. Relation is a bitset of the 2**k visible words."""
    width(k)
    if type(relation) is not int or not 0 <= relation < 1 << (1 << k):
        raise ValueError("relation bitset outside the visible cube")
    count = relation.bit_count()
    if not count or count & (count - 1):
        return False
    anchor = (relation & -relation).bit_length() - 1
    basis = {}
    rest = relation
    while rest:
        bit = rest & -rest
        rest -= bit
        vector = (bit.bit_length() - 1) ^ anchor
        while vector:
            pivot = vector.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = vector
                break
            vector ^= basis[pivot]
    return count == 1 << len(basis)


def canonical_chain(k):
    """A maximal alternating chain; stage zero (not returned) is empty."""
    width(k)
    if k <= 1:
        return [(1 << (1 << k)) - 1]
    stages = [1, (1 << 0) | (1 << 1) | (1 << 2), (1 << 4) - 1]
    for dimension in range(3, k + 1):
        previous_space = (1 << (1 << (dimension - 1))) - 1
        stages += [previous_space | (1 << (1 << (dimension - 1))),
                   (1 << (1 << dimension)) - 1]
    return stages


def chain_record(k):
    """Backward subset-lattice DP: maximum number of property changes."""
    width(k)
    size = 1 << (1 << k)
    accepted = bytearray(affine_by_rank(mask, k) for mask in range(size))
    depths = bytearray(size)
    for mask in range(1, size):
        rest = mask
        best = 0
        while rest:
            bit = rest & -rest
            rest -= bit
            previous = mask ^ bit
            best = max(best, depths[previous] + (accepted[mask] != accepted[previous]))
        depths[mask] = best
    return {"visible_width": k, "affinity_bits": "".join(map(str, accepted)),
            "depths": list(depths), "canonical_chain": canonical_chain(k)}


def reduce_sat_prefix(k, sources):
    """A total reduction from nested difference of d=max(1,2k-1) SAT inputs.

    Hidden selectors choose one visible point. Its entry stage i activates
    the first i source CNFs, whose variable blocks are mutually disjoint.
    Arbitrary SAT truth patterns are allowed; no nesting promise is required.
    """
    width(k)
    d = max(1, 2*k - 1)
    if not isinstance(sources, (list, tuple)) or len(sources) != d:
        raise ValueError("wrong number of SAT instances for this fixed width")
    sources = [source(spec) for spec in sources]
    stages = canonical_chain(k)
    points = 1 << k
    selectors = list(range(k, k + points))
    next_variable = k + points
    blocks = []
    for spec in sources:
        blocks.append(list(range(next_variable, next_variable + spec["nvars"])))
        next_variable += spec["nvars"]
    entries = [next(i + 1 for i, stage in enumerate(stages) if stage >> x & 1)
               for x in range(points)]
    clauses = [[selector + 1 for selector in selectors]]
    for x, selector in enumerate(selectors):
        for bit in range(k):
            clauses.append([-selector - 1, bit + 1 if x >> bit & 1 else -bit - 1])
        for i in range(entries[x]):
            for row in sources[i]["clauses"]:
                clauses.append([-selector - 1] +
                               [(blocks[i][abs(lit) - 1] + 1) * (1 if lit > 0 else -1)
                                for lit in row])
    return {"schema": REDUCTION_SCHEMA, "visible_width": k, "sources": sources,
            "input_sha256": source_digest(k, sources), "nvars": next_variable,
            "clauses": clauses, "selectors": selectors, "source_variables": blocks,
            "entry_stage": entries, "canonical_chain": stages}


def satisfies(clauses, word):
    return all(any(bool(word >> (abs(lit) - 1) & 1) == (lit > 0) for lit in row)
               for row in clauses)


def reduction_record(k, sources):
    gadget = reduce_sat_prefix(k, sources)
    n = gadget["nvars"]
    if n > MAX_EXHAUSTIVE_VARIABLES:
        raise ValueError("gadget exceeds the explicit assignment enumeration cap")
    truth = []
    source_evaluations = 0
    for spec in gadget["sources"]:
        answers = [satisfies(spec["clauses"], word) for word in range(1 << spec["nvars"])]
        source_evaluations += len(answers)
        truth.append(any(answers))
    prefix = 0
    for answer in truth:
        if not answer:
            break
        prefix += 1
    relation = 0
    for assignment in range(1 << n):
        if satisfies(gadget["clauses"], assignment):
            relation |= 1 << (assignment & ((1 << k) - 1))
    expected = gadget["canonical_chain"][prefix - 1] if prefix else 0
    if relation != expected or affine_by_rank(relation, k) != bool(prefix % 2):
        raise ValueError("reduction failed its exact original-assignment control")
    return {"gadget": gadget, "source_sat": truth, "longest_sat_prefix": prefix,
            "projection": relation, "projection_affine": affine_by_rank(relation, k),
            "source_formula_evaluations": source_evaluations,
            "gadget_formula_evaluations": 1 << n}


def campaign():
    # Four zero-visible controls include empty formulas, clauses, and hidden models.
    for spec in ({"nvars": 0, "clauses": []}, {"nvars": 0, "clauses": [[]]},
                 {"nvars": 1, "clauses": [[1]]},
                 {"nvars": 1, "clauses": [[1], [-1]]}):
        yield 0, [spec]
    # All 512 two-variable CNFs over distinct non-tautological clauses.
    pool = [[(i + 1)*sign for i, sign in enumerate(signs) if sign]
            for signs in product((-1, 0, 1), repeat=2)]
    for selection in range(1 << len(pool)):
        yield 1, [{"nvars": 2, "clauses": [row for i, row in enumerate(pool)
                                          if selection >> i & 1]}]
    # Every triple of one-variable CNFs over empty, positive, negative clauses.
    one_pool = [[], [1], [-1]]
    one_sources = [{"nvars": 1, "clauses": [row for i, row in enumerate(one_pool)
                                          if selection >> i & 1]}
                   for selection in range(8)]
    for triple in product(range(8), repeat=3):
        yield 2, [one_sources[i] for i in triple]
    # Every unconstrained SAT truth pattern for the five-source width-three map.
    for pattern in range(32):
        yield 3, [{"nvars": 0, "clauses": [] if pattern >> i & 1 else [[]]}
                  for i in range(5)]


def build_artifact():
    return {"schema": SCHEMA, "convention": "nonempty_affine",
            "chains": [chain_record(k) for k in range(5)],
            "reductions": [reduction_record(k, specs) for k, specs in campaign()]}
