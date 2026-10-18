"""Independent replay of the proof-DAG invented-relation bridge."""

from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).parent


def lit_value(lit, assignment):
    v = abs(lit) - 1
    return assignment[v] if lit > 0 else not assignment[v]


def sat(clauses, assignment):
    return all(any(lit_value(l, assignment) for l in c) for c in clauses)


def projected_relation(clauses, shared):
    mentioned = {abs(l) - 1 for c in clauses for l in c}
    local = sorted(mentioned - set(shared))
    rows = []
    for sbits in product((False, True), repeat=len(shared)):
        ok = False
        for lbits in product((False, True), repeat=len(local)):
            assignment = dict(zip(shared, sbits)); assignment.update(zip(local, lbits))
            if sat(clauses, assignment):
                ok = True
                break
        rows.append(int(ok))
    return tuple(rows)


def candidate_value(candidate, assignment):
    kind = candidate["kind"]
    if kind == "UNIT":
        return bool(assignment[candidate["var"]]) == bool(candidate["value"])
    if kind == "XOR":
        return (sum(assignment[v] for v in candidate["support"]) & 1) == int(candidate["rhs"])
    if kind == "PB":
        lhs = sum(int(w) * int(assignment[int(v)]) for v, w in candidate["weights"].items())
        return lhs <= int(candidate["bound"]) if candidate["sense"] == "<=" else lhs >= int(candidate["bound"])
    if kind == "TRUTH_TABLE":
        idx = 0
        for v in candidate["support"]:
            idx = (idx << 1) | int(bool(assignment[v]))
        return bool((int(candidate["accepted_mask"]) >> idx) & 1)
    raise AssertionError(kind)


def normalize_clause(clause):
    vals = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    assert not any(-x in vals for x in vals)
    return vals


def resolve(left, right, pivot):
    p = int(pivot) + 1
    a = set(left); b = set(right)
    if p in a and -p in b:
        out = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        out = (a - {-p}) | (b - {p})
    else:
        raise AssertionError((left, right, pivot))
    return normalize_clause(out)


def replay_proof(certificate):
    A = {normalize_clause(c) for c in certificate["A"]}
    B = {normalize_clause(c) for c in certificate["B"]}
    nodes = []
    for node in certificate["nodes"]:
        clause = normalize_clause(node["clause"])
        if "part" in node:
            assert node["part"] in ("A", "B")
            assert clause in (A if node["part"] == "A" else B)
        else:
            assert clause == resolve(nodes[node["left"]], nodes[node["right"]], node["pivot"])
        nodes.append(clause)
    return nodes


def main():
    artifact = json.loads((ROOT / "PROOF_PORTFOLIO_BRIDGE.json").read_text(encoding="utf-8"))
    bridge = artifact["bridge"]
    assert artifact["all_checks_passed"]
    assert bridge["proof_empty_clause"] == []
    replayed_nodes = replay_proof(bridge["proof_certificate"])
    assert len(replayed_nodes) == bridge["proof_nodes"]
    assert replayed_nodes[-1] == ()
    assert bridge["positive_unit_nodes"] == bridge["groups"]
    assert bridge["raw_interpolant_literals"] == bridge["groups"]
    assert bridge["symbolic_check"]
    assert len(set(bridge["representatives"])) == bridge["groups"]
    for row in bridge["unit_fragments"]:
        clauses = tuple(tuple(c) for c in row["clauses"])
        shared = tuple(row["shared"])
        relation = projected_relation(clauses, shared)
        assert relation == tuple(row["relation_bits"])
        assert relation == (0, 1)
        assert row["candidate"]["kind"] == "UNIT"
        assert row["candidate"]["var"] == row["representative"]
        assert row["candidate"]["value"] is True
        assert sorted(c["kind"] for c in row["candidates"]) == row["candidate_kinds"]
        for candidate in row["candidates"]:
            for bits, expected in zip(product((False, True), repeat=len(shared)), relation):
                assignment = dict(zip(shared, bits))
                assert int(candidate_value(candidate, assignment)) == expected
        assert row["leaf_count"] == 4
        assert row["visited_nodes"] == 7

    reps = bridge["representatives"]
    groups = bridge["groups"]
    assert (sum(1 for _ in reps) & 1) == (groups & 1)
    assert (1 - (groups & 1)) != (groups & 1)
    hard = artifact["hard_control"]
    assert hard["status"] == "UNKNOWN"
    assert hard["shared_count"] > hard["max_shared"]
    scale = artifact["scale_check"]
    assert scale == {"groups": 256, "width": 8, "proof_nodes": 4097,
                     "positive_unit_nodes": 256, "raw_interpolant_literals": 256,
                     "symbolic_check": True}
    scan = artifact["subdag_scan"]
    assert scan["considered_nodes"] == 42
    assert scan["status_counts"] == {"FOUND": 16, "NO_COMPACT": 24, "UNKNOWN": 2}
    assert scan["candidate_kind_counts"] == {"PB": 8, "TRUTH_TABLE": 24, "UNIT": 8}
    print(json.dumps({"independent_checks_passed": True,
                      "unit_fragments": len(bridge["unit_fragments"]),
                      "hard_control": hard["status"]}))


if __name__ == "__main__":
    main()
