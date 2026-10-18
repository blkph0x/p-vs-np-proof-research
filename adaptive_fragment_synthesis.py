"""Bounded, certificate-producing relation synthesis for proof fragments.

This module is deliberately a bounded experiment.  It projects a small CNF
fragment onto a declared shared interface, proposes a few exact languages, and
recomputes the projection in an independent checker.  The projection and all
candidate discovery are capped; an over-budget request returns ``UNKNOWN``.
There is no unrestricted equivalence or SAT oracle hidden here.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product, permutations
import math


def norm_clause(clause):
    vals = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-x in vals for x in vals):
        return None
    return vals


def var(lit):
    return abs(int(lit)) - 1


def eval_clause(clause, assignment):
    return any((assignment[var(lit)] if lit > 0 else not assignment[var(lit)]) for lit in clause)


def eval_cnf(clauses, assignment):
    return all(eval_clause(c, assignment) for c in clauses)


@dataclass(frozen=True)
class SynthesisResult:
    status: str
    candidate: dict | None
    all_candidates: tuple
    shared: tuple
    local: tuple
    relation_bits: tuple
    discovery_work: int
    reason: str | None = None


def extract_proof_leaves(proof, root, max_nodes=256):
    """Extract the leaf CNF fragment of a bounded proof-DAG subgraph.

    The helper accepts the small proof-DAG shape used by the motif miner
    (``kind=leaf``/``kind=res``). It returns ``None`` when the visited subgraph
    exceeds the explicit cap instead of silently dropping proof ancestors.
    """
    seen = set()
    leaves = []

    def visit(index):
        if index in seen:
            return True
        seen.add(index)
        if len(seen) > max_nodes:
            return False
        node = proof.nodes[index]
        if node.get("kind") == "leaf" or "part" in node:
            leaves.append(tuple(node["clause"]))
            return True
        if not (node.get("kind") == "res" or ("left" in node and "right" in node)):
            return False
        return visit(node["left"]) and visit(node["right"])

    if not visit(root):
        return None
    return tuple(leaves), len(seen)


def _truth_bit(candidate, assignment):
    kind = candidate["kind"]
    if kind == "UNIT":
        return bool(assignment[candidate["var"]]) == bool(candidate["value"])
    if kind == "XOR":
        return (sum(assignment[v] for v in candidate["support"]) & 1) == candidate["rhs"]
    if kind == "PB":
        lhs = sum(int(w) * int(assignment[v]) for v, w in candidate["weights"].items())
        return lhs <= candidate["bound"] if candidate["sense"] == "<=" else lhs >= candidate["bound"]
    if kind == "ITE":
        expected = assignment[candidate["a"]] if assignment[candidate["c"]] else assignment[candidate["b"]]
        return bool(assignment[candidate["z"]]) == bool(expected)
    if kind == "TRUTH_TABLE":
        index = 0
        for i, v in enumerate(candidate["support"]):
            # ``product(False, True, repeat=n)`` enumerates the first
            # coordinate most-significant, so use the same convention here.
            index = (index << 1) | int(bool(assignment[v]))
        return bool((candidate["accepted_mask"] >> index) & 1)
    raise ValueError(kind)


def _bits_for_candidate(candidate, nvars):
    b = max(1, math.ceil(math.log2(max(2, nvars))))
    k = candidate["kind"]
    if k == "UNIT":
        return 8 + b + 1
    if k == "XOR":
        return 8 + len(candidate["support"]) * b + 1
    if k == "PB":
        return 8 + len(candidate["weights"]) * (b + 2) + b + 2
    if k == "ITE":
        return 8 + 4 * b
    if k == "TRUTH_TABLE":
        return 8 + len(candidate["support"]) * b + (1 << len(candidate["support"]))
    raise ValueError(k)


def _relation_projection(clauses, shared, local, max_assignments):
    total = (1 << len(shared)) * (1 << len(local))
    if total > max_assignments:
        return None, total
    bits = []
    for sbits in product((False, True), repeat=len(shared)):
        found = False
        for lbits in product((False, True), repeat=len(local)):
            a = dict(zip(shared, sbits))
            a.update(zip(local, lbits))
            if eval_cnf(clauses, a):
                found = True
                break
        bits.append(int(found))
    return tuple(bits), total


def _mask_from_bits(bits):
    # The integer index computed in ``_truth_bit`` is exactly the position in
    # the product enumeration, so store relation bit i at bit position i.
    return sum(int(x) << i for i, x in enumerate(bits))


def _same_relation(candidate, shared, relation_bits):
    for i, sbits in enumerate(product((False, True), repeat=len(shared))):
        a = dict(zip(shared, sbits))
        if int(_truth_bit(candidate, a)) != relation_bits[i]:
            return False
    return True


def _discover_candidates(shared, relation_bits, max_truth_table_bits=12):
    out = []
    n = len(shared)
    # Unit candidates are useful for OR-collapse fragments.
    for v in shared:
        for value in (False, True):
            c = {"kind": "UNIT", "var": v, "value": value}
            if _same_relation(c, shared, relation_bits):
                out.append(c)
    # One affine equation over the interface.
    for mask in range(1, 1 << n):
        support = tuple(shared[i] for i in range(n) if (mask >> i) & 1)
        for rhs in (0, 1):
            c = {"kind": "XOR", "support": support, "rhs": rhs}
            if _same_relation(c, shared, relation_bits):
                out.append(c)
    # Small nonnegative cardinality inequalities.  Weight search is intentionally
    # bounded to 0/1; arbitrary PB recognition remains outside this experiment.
    for sense in ("<=", ">="):
        for bound in range(n + 1):
            c = {"kind": "PB", "weights": {v: 1 for v in shared}, "sense": sense, "bound": bound}
            if _same_relation(c, shared, relation_bits):
                out.append(c)
    # Exact four-variable ITE relation, with all role assignments checked.
    if n == 4:
        for z, cvar, av, bv in permutations(shared, 4):
            c = {"kind": "ITE", "z": z, "c": cvar, "a": av, "b": bv}
            if _same_relation(c, shared, relation_bits):
                out.append(c)
    if n <= max_truth_table_bits:
        out.append({"kind": "TRUTH_TABLE", "support": tuple(shared), "accepted_mask": _mask_from_bits(relation_bits)})
    # Deduplicate candidates that arise from syntactically different searches.
    uniq = {}
    for c in out:
        key = repr(sorted(c.items()))
        uniq[key] = c
    return tuple(uniq.values())


def _candidate_search_work(n, max_truth_table_bits):
    """Count bounded truth-table evaluations used by the fixed vocabulary."""
    candidate_count = 2 * n                         # units
    candidate_count += 2 * ((1 << n) - 1)           # one XOR support, two RHSs
    candidate_count += 2 * (n + 1)                  # unweighted PB thresholds
    if n == 4:
        candidate_count += 24                       # all ITE role permutations
    if n <= max_truth_table_bits:
        candidate_count += 1                        # explicit truth-table fallback
    return (1 << n) * candidate_count


def synthesize_fragment(clauses, shared, *, max_shared=6, max_local=6,
                        max_assignments=1 << 16, max_truth_table_bits=12):
    """Discover exact bounded candidates for ``exists local . CNF(clauses)``.

    ``shared`` is part of the certificate interface and must contain every
    variable that a returned candidate mentions.  The result status is one of
    ``FOUND``, ``NO_COMPACT`` or ``UNKNOWN``.  ``NO_COMPACT`` still includes a
    truth-table candidate when the interface is below the explicit table cap.
    """
    clauses = tuple(norm_clause(c) for c in clauses)
    if any(c is None for c in clauses):
        return SynthesisResult("UNKNOWN", None, (), (), (), (), 0, "tautological clause is not a relation witness")
    shared = tuple(dict.fromkeys(int(v) for v in shared))
    mentioned = sorted({var(l) for c in clauses for l in c})
    local = tuple(v for v in mentioned if v not in shared)
    if len(shared) > max_shared:
        return SynthesisResult("UNKNOWN", None, (), shared, local, (), 0, "shared interface exceeds bound")
    if len(local) > max_local:
        return SynthesisResult("UNKNOWN", None, (), shared, local, (), 0, "local projection exceeds bound")
    relation, assignments = _relation_projection(clauses, shared, local, max_assignments)
    if relation is None:
        return SynthesisResult("UNKNOWN", None, (), shared, local, (), assignments, "projection assignment budget exceeded")
    candidates = _discover_candidates(shared, relation, max_truth_table_bits)
    # Candidate cost includes the complete projection work.  This makes the
    # bounded semantic search visible rather than silently treating discovery as free.
    total_work = assignments * max(1, len(clauses)) + _candidate_search_work(len(shared), max_truth_table_bits)
    for c in candidates:
        c["representation_bits"] = _bits_for_candidate(c, max(1, max(mentioned + [0]) + 1))
        c["discovery_work"] = total_work
    compact = [c for c in candidates if c["kind"] != "TRUTH_TABLE"]
    status = "FOUND" if compact else "NO_COMPACT"
    chosen = min(compact or list(candidates), key=lambda c: (c["representation_bits"], c["kind"])) if candidates else None
    return SynthesisResult(status, chosen, tuple(candidates), shared, local, relation,
                           total_work, None if candidates else "no bounded language matched")


def verify_synthesis(result, clauses):
    """Independent certificate replay; recomputes projection and candidate truth table."""
    if result.status == "UNKNOWN":
        return result.candidate is None and not result.all_candidates
    relation, _ = _relation_projection(tuple(norm_clause(c) for c in clauses), result.shared, result.local, 1 << 30)
    if relation is None or tuple(relation) != tuple(result.relation_bits):
        return False
    for c in result.all_candidates:
        if set(c.get("support", ())) - set(result.shared):
            return False
        if not _same_relation(c, result.shared, relation):
            return False
    if result.candidate is not None and result.candidate not in result.all_candidates:
        return False
    return True


def result_dict(result):
    return {
        "status": result.status,
        "candidate": result.candidate,
        "candidates": list(result.all_candidates),
        "candidate_kinds": sorted(c["kind"] for c in result.all_candidates),
        "shared": list(result.shared),
        "local": list(result.local),
        "relation_bits": list(result.relation_bits),
        "discovery_work": result.discovery_work,
        "reason": result.reason,
    }
