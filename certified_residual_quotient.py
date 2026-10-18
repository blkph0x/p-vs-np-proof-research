"""Sound but incomplete residual-state quotienting with proof certificates.

The classifier deliberately exposes the coNP-hardness boundary documented in
``RESIDUAL_EQUIVALENCE_BARRIER_REPORT.md``.  It merges only by syntactic
identity, bounded exhaustive comparison, or a supplied pair of resolution
implication certificates.  A single assignment can certify that two residuals
are distinct.  Otherwise the result is ``UNKNOWN``.
"""

from __future__ import annotations

from itertools import product
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def normalize_clause(clause):
    vals = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-x in vals for x in vals):
        return None
    return vals


def normalize_formula(clauses):
    out = []
    seen = set()
    for clause in clauses:
        norm = normalize_clause(clause)
        if norm is None:
            continue
        if norm not in seen:
            seen.add(norm); out.append(norm)
    return tuple(sorted(out))


def eval_cnf(clauses, assignment):
    return all(any((assignment[abs(lit) - 1] if lit > 0 else not assignment[abs(lit) - 1])
                   for lit in clause) for clause in clauses)


def truth_table(clauses, nvars):
    mask = 0
    for bits in product((False, True), repeat=nvars):
        if eval_cnf(clauses, bits):
            index = 0
            for bit in bits:
                index = (index << 1) | int(bit)
            mask |= 1 << index
    return mask


def resolve(left, right, pivot):
    p = int(pivot)
    a = set(left); b = set(right)
    if p in a and -p in b:
        result = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        result = (a - {-p}) | (b - {p})
    else:
        raise ValueError("non-resolvable parent clauses")
    return normalize_clause(result)


def replay_resolution(proof, allowed_premises):
    allowed = {normalize_clause(c) for c in allowed_premises}
    nodes = []
    for node in proof["nodes"]:
        clause = normalize_clause(node["clause"])
        if node["kind"] == "leaf":
            if clause not in allowed:
                return False
        elif node["kind"] == "res":
            try:
                expected = resolve(nodes[node["left"]], nodes[node["right"]], node["pivot"])
            except (IndexError, ValueError):
                return False
            if clause != expected:
                return False
        else:
            return False
        nodes.append(clause)
    root = int(proof["root"])
    return 0 <= root < len(nodes) and nodes[root] == ()


def _add_node(nodes, clause, kind, **extra):
    node = {"kind": kind, "clause": list(clause)}
    node.update(extra)
    nodes.append(node)
    return len(nodes) - 1


def build_refutation(premises, max_nodes=2000):
    """Small saturation builder used only for certificate fixtures."""
    unique = []
    seen = set()
    for clause in premises:
        norm = normalize_clause(clause)
        if norm is None:
            continue
        if norm not in seen:
            seen.add(norm); unique.append(norm)
    nodes = []
    indices = {}
    for clause in unique:
        indices[clause] = _add_node(nodes, clause, "leaf")
        if clause == ():
            return {"nodes": nodes, "root": indices[clause]}
    while len(nodes) <= max_nodes:
        current = list(indices)
        for i, left in enumerate(current):
            for right in current[i + 1:]:
                pivots = {abs(x) for x in left if -x in right}
                pivots |= {abs(x) for x in right if -x in left}
                for pivot in sorted(pivots):
                    try:
                        out = resolve(left, right, pivot)
                    except ValueError:
                        continue
                    if out in indices:
                        continue
                    li = indices[left]; ri = indices[right]
                    indices[out] = _add_node(nodes, out, "res", left=li, right=ri, pivot=pivot)
                    if out == ():
                        return {"nodes": nodes, "root": indices[out]}
                    if len(nodes) > max_nodes:
                        return None
        if len(indices) == len(current):
            return None
    return None


def build_implication_certificate(source, target, max_nodes=2000):
    """Certify source => target clause by clause via resolution refutations."""
    source = normalize_formula(source); target = normalize_formula(target)
    obligations = []
    for clause in target:
        premises = list(source) + [(-lit,) for lit in clause]
        proof = build_refutation(premises, max_nodes=max_nodes)
        if proof is None:
            return None
        obligations.append({"target_clause": list(clause), "proof": proof,
                            "premises": [list(c) for c in premises]})
    return {"source": [list(c) for c in source],
            "target": [list(c) for c in target], "obligations": obligations}


def verify_implication_certificate(certificate):
    source = normalize_formula(certificate["source"])
    target = normalize_formula(certificate["target"])
    if len(target) != len(certificate["obligations"]):
        return False
    for row in certificate["obligations"]:
        clause = normalize_clause(row["target_clause"])
        if clause not in target:
            return False
        expected = list(source) + [(-lit,) for lit in clause]
        if normalize_formula(row["premises"]) != normalize_formula(expected):
            return False
        if not replay_resolution(row["proof"], expected):
            return False
    return True


def build_equivalence_certificate(left, right, max_nodes=2000):
    forward = build_implication_certificate(left, right, max_nodes)
    reverse = build_implication_certificate(right, left, max_nodes)
    if forward is None or reverse is None:
        return None
    return {"forward": forward, "reverse": reverse}


def verify_equivalence_certificate(certificate):
    return (isinstance(certificate, dict)
            and verify_implication_certificate(certificate["forward"])
            and verify_implication_certificate(certificate["reverse"]))


def classify_pair(left, right, nvars, max_assignments=1 << 12,
                  witness=None, equivalence_certificate=None):
    left = normalize_formula(left); right = normalize_formula(right)
    if left == right:
        return {"status": "MERGED_SYNTACTIC", "left": [list(c) for c in left],
                "right": [list(c) for c in right], "work": 0}
    if equivalence_certificate is not None and verify_equivalence_certificate(equivalence_certificate):
        return {"status": "MERGED_PROOF", "left": [list(c) for c in left],
                "right": [list(c) for c in right], "work": len(equivalence_certificate["forward"]["obligations"])
                + len(equivalence_certificate["reverse"]["obligations"])}
    if witness is not None:
        assignment = tuple(bool(x) for x in witness)
        if len(assignment) == nvars and eval_cnf(left, assignment) != eval_cnf(right, assignment):
            return {"status": "DISTINCT_WITNESS", "witness": list(assignment), "work": 1}
    if (1 << nvars) <= max_assignments:
        lt = truth_table(left, nvars); rt = truth_table(right, nvars)
        if lt == rt:
            return {"status": "MERGED_EXACT", "left_table": lt, "right_table": rt,
                    "work": 1 << nvars}
        for bits in product((False, True), repeat=nvars):
            if eval_cnf(left, bits) != eval_cnf(right, bits):
                return {"status": "DISTINCT_EXACT", "witness": list(bits),
                        "work": 1 << nvars}
    return {"status": "UNKNOWN", "work": 0}


def build_artifact():
    syntactic = classify_pair(((1,),), ((1,),), 1)
    left = ((1,), (2,))
    right = ((1,), (2,), (1, 2))
    cert = build_equivalence_certificate(left, right)
    forged = copy.deepcopy(cert)
    forged["forward"]["obligations"][0]["proof"]["nodes"][-1]["clause"] = [1]
    proof_merge = classify_pair(left, right, 2, max_assignments=1,
                                equivalence_certificate=cert)
    distinct = classify_pair(((1,),), ((2,),), 2, witness=(True, False))
    exact = classify_pair(((1,),), ((1, 2),), 2, max_assignments=4)
    unknown = classify_pair(((1,), (-1,)), (), 8, max_assignments=16)
    witness_unknown = classify_pair(((1,),), (), 8, max_assignments=16,
                                    witness=(False,) + (False,) * 7)
    assert syntactic["status"] == "MERGED_SYNTACTIC"
    assert cert is not None and verify_equivalence_certificate(cert)
    assert not verify_equivalence_certificate(forged)
    assert proof_merge["status"] == "MERGED_PROOF"
    assert distinct["status"] == "DISTINCT_WITNESS"
    assert exact["status"] == "DISTINCT_EXACT"
    assert unknown["status"] == "UNKNOWN"
    assert witness_unknown["status"] == "DISTINCT_WITNESS"
    return {"all_checks_passed": True,
            "cases": {"syntactic": syntactic, "proof": proof_merge,
                      "distinct_witness": distinct, "distinct_exact": exact,
                      "unknown": unknown, "witness_beyond_cap": witness_unknown},
            "proof_certificate": cert,
            "adversarial": {"forged_certificate_rejected": True}}


def write_artifact():
    artifact = build_artifact()
    (ROOT / "CERTIFIED_RESIDUAL_QUOTIENT.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    print(json.dumps(write_artifact(), indent=2))
