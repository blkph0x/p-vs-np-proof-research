"""Independent replay of repeated proof-DAG template discovery."""

from __future__ import annotations

from collections import Counter, OrderedDict
import copy
import json
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def norm_clause(clause):
    vals = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    assert not any(-x in vals for x in vals)
    return vals


def boundary_for_clause(clause):
    return tuple(sorted({abs(int(lit)) - 1 for lit in clause}))


def literal_value(lit, assignment):
    value = assignment[abs(lit) - 1]
    return bool(value) if lit > 0 else not bool(value)


def sat(clauses, assignment):
    return all(any(literal_value(lit, assignment) for lit in clause) for clause in clauses)


def replay_proof(certificate):
    a = {norm_clause(clause) for clause in certificate["A"]}
    b = {norm_clause(clause) for clause in certificate["B"]}
    nodes = []
    for row in certificate["nodes"]:
        clause = norm_clause(row["clause"])
        if "part" in row:
            assert row["part"] in ("A", "B")
            assert clause in (a if row["part"] == "A" else b)
        else:
            left = set(nodes[int(row["left"])])
            right = set(nodes[int(row["right"])])
            pivot = int(row["pivot"]) + 1
            if pivot in left and -pivot in right:
                derived = (left - {pivot}) | (right - {-pivot})
            elif -pivot in left and pivot in right:
                derived = (left - {-pivot}) | (right - {pivot})
            else:
                raise AssertionError("invalid resolution pivot")
            assert clause == norm_clause(derived)
        nodes.append(clause)
    return nodes


def extract_leaves(nodes, root, max_nodes):
    seen = set()
    leaves = []

    def visit(index):
        index = int(index)
        if index in seen:
            return True
        seen.add(index)
        if len(seen) > max_nodes:
            return False
        row = nodes[index]
        if "part" in row:
            leaves.append(norm_clause(row["clause"]))
            return True
        return visit(row["left"]) and visit(row["right"])

    if not visit(root):
        return None
    return tuple(leaves), len(seen)


def projection(clauses, shared, local):
    bits = []
    for sbits in product((False, True), repeat=len(shared)):
        found = False
        for lbits in product((False, True), repeat=len(local)):
            assignment = [False] * (max(shared + local + (-1,)) + 1)
            for variable, value in zip(shared, sbits):
                assignment[variable] = value
            for variable, value in zip(local, lbits):
                assignment[variable] = value
            if sat(clauses, assignment):
                found = True
                break
        bits.append(int(found))
    return tuple(bits)


def candidate_value(candidate, assignment):
    kind = candidate["kind"]
    if kind == "UNIT":
        return bool(assignment[int(candidate["var"])]) == bool(candidate["value"])
    if kind == "XOR":
        return (sum(assignment[int(v)] for v in candidate["support"]) & 1) == int(candidate["rhs"])
    if kind == "PB":
        lhs = sum(int(weight) * int(assignment[int(variable)])
                  for variable, weight in candidate["weights"].items())
        return lhs <= int(candidate["bound"]) if candidate["sense"] == "<=" else lhs >= int(candidate["bound"])
    if kind == "ITE":
        expected = assignment[int(candidate["a"])] if assignment[int(candidate["c"])] else assignment[int(candidate["b"])]
        return bool(assignment[int(candidate["z"])]) == bool(expected)
    if kind == "TRUTH_TABLE":
        index = 0
        for variable in candidate["support"]:
            index = (index << 1) | int(bool(assignment[int(variable)]))
        return bool((int(candidate["accepted_mask"]) >> index) & 1)
    raise AssertionError(kind)


def candidate_matches(candidate, shared, relation_bits):
    for bits, expected in zip(product((False, True), repeat=len(shared)), relation_bits):
        assignment = dict(zip(shared, bits))
        assert int(candidate_value(candidate, assignment)) == int(expected)
    return True


def canonical_candidate(candidate, shared):
    positions = {int(variable): index for index, variable in enumerate(shared)}
    kind = candidate["kind"]
    if kind == "UNIT":
        return {"kind": kind, "var": positions[int(candidate["var"])],
                "value": bool(candidate["value"])}
    if kind == "XOR":
        return {"kind": kind, "support": [positions[int(v)] for v in candidate["support"]],
                "rhs": int(candidate["rhs"])}
    if kind == "PB":
        weights = {str(positions[int(v)]): int(w) for v, w in candidate["weights"].items()}
        return {"kind": kind, "weights": dict(sorted(weights.items(), key=lambda item: int(item[0]))),
                "sense": candidate["sense"], "bound": int(candidate["bound"])}
    if kind == "ITE":
        return {"kind": kind, "z": positions[int(candidate["z"])],
                "c": positions[int(candidate["c"])],
                "a": positions[int(candidate["a"])],
                "b": positions[int(candidate["b"])]}
    if kind == "TRUTH_TABLE":
        return {"kind": kind,
                "support": [positions[int(v)] for v in candidate["support"]],
                "accepted_mask": int(candidate["accepted_mask"])}
    raise AssertionError(kind)


def fixed_candidate_search_work(shared_count, max_truth_table_bits=12):
    n = int(shared_count)
    candidate_count = 2 * n + 2 * ((1 << n) - 1) + 2 * (n + 1)
    if n == 4:
        candidate_count += 24
    if n <= max_truth_table_bits:
        candidate_count += 1
    return (1 << n) * candidate_count


def signature(row):
    return json.dumps({"status": row["status"],
                       "candidate": row["canonical_candidate"],
                       "relation_bits": row["relation_bits"]}, sort_keys=True)


def verify_record(row, nodes, max_nodes, max_local):
    clause = norm_clause(row["clause"])
    boundary = boundary_for_clause(clause)
    assert tuple(row["boundary"]) == boundary
    if row["status"] == "UNKNOWN":
        assert row["candidate"] is None and row["candidates"] == []
        if row["unknown_stage"] == "subdag_cap":
            assert extract_leaves(nodes, row["node_index"], max_nodes) is None
        else:
            assert row["unknown_stage"] == "projection_cap"
            extracted = extract_leaves(nodes, row["node_index"], max_nodes)
            assert extracted is not None
            leaves, visited = extracted
            assert visited == row["visited_nodes"]
            assert [list(c) for c in leaves] == row["leaf_clauses"]
            mentioned = sorted({abs(lit) - 1 for c in leaves for lit in c})
            local = tuple(variable for variable in mentioned if variable not in boundary)
            assert list(local) == row["local"]
            assert len(local) > max_local or "budget" in row["reason"]
        return
    extracted = extract_leaves(nodes, row["node_index"], max_nodes)
    assert extracted is not None
    leaves, visited = extracted
    assert visited == row["visited_nodes"]
    assert [list(c) for c in leaves] == row["leaf_clauses"]
    mentioned = sorted({abs(lit) - 1 for c in leaves for lit in c})
    local = tuple(variable for variable in mentioned if variable not in boundary)
    assert list(local) == row["local"]
    relation = projection(leaves, boundary, local)
    assert list(relation) == row["relation_bits"]
    for candidate in row["candidates"]:
        assert set(int(v) for v in candidate.get("support", ())) <= set(boundary)
        assert candidate_matches(candidate, boundary, relation)
    assert row["candidate"] in row["candidates"]
    assert candidate_matches(row["candidate"], boundary, relation)
    compact = [candidate for candidate in row["candidates"] if candidate["kind"] != "TRUTH_TABLE"]
    assert row["status"] == ("FOUND" if compact else "NO_COMPACT")
    assert row["canonical_candidate"] == canonical_candidate(row["candidate"], boundary)
    assert row["template_key"] == signature(row)
    projection_work = (1 << (len(boundary) + len(local))) * max(1, len(leaves))
    search_work = fixed_candidate_search_work(len(boundary))
    assert row["projection_work"] == projection_work
    assert row["candidate_search_work"] == search_work
    assert row["template_check_work"] == (1 << len(boundary))
    assert row["naive_work"] == projection_work + search_work


def verify_block(block, expected_proof_nodes=None):
    """Replay one serialized scan block, including all template accounting."""
    assert block["all_checks_passed"]
    parameters = block["parameters"]
    nodes = replay_proof(block["proof_certificate"])
    if expected_proof_nodes is not None:
        assert len(nodes) == expected_proof_nodes
    assert len(nodes) == block["proof_nodes"]
    assert nodes[int(block["proof_root"])] == ()
    serialized_nodes = block["proof_certificate"]["nodes"]
    for row in block["records"]:
        verify_record(row, serialized_nodes, parameters["max_nodes"], parameters["max_local"])
    status_counts = Counter(row["status"] for row in block["records"])
    kind_counts = Counter(row["candidate"]["kind"] for row in block["records"]
                          if row["candidate"] is not None)
    assert dict(sorted(status_counts.items())) == block["status_counts"]
    assert dict(sorted(kind_counts.items())) == block["candidate_kind_counts"]

    groups = OrderedDict()
    for row in block["records"]:
        if row["template_key"] is not None:
            groups.setdefault(row["template_key"], []).append(row)
    assert len(groups) == len(block["template_groups"])
    for expected, (key, rows) in zip(block["template_groups"], groups.items()):
        assert expected["template_key"] == key
        assert expected["occurrences"] == len(rows)
        assert expected["proof_nodes"] == [row["node_index"] for row in rows]
        naive = sum(row["naive_work"] for row in rows)
        reused = rows[0]["naive_work"] + sum(
            row["projection_work"] + row["template_check_work"] for row in rows[1:])
        assert expected["naive_work"] == naive
        assert expected["reused_work"] == reused
        assert expected["saved_work"] == naive - reused
        assert expected["saved_work"] > 0

    candidate_rows = [row for row in block["records"] if row["candidate"] is not None]
    if candidate_rows:
        forged = copy.deepcopy(candidate_rows[0]["candidate"])
        if forged["kind"] == "UNIT":
            forged["value"] = not bool(forged["value"])
        elif forged["kind"] == "PB":
            forged["bound"] = int(forged["bound"]) + 1
        elif forged["kind"] == "XOR":
            forged["rhs"] = 1 - int(forged["rhs"])
        else:
            forged["accepted_mask"] = int(forged["accepted_mask"]) ^ 1
        forged_rejected = False
        try:
            candidate_matches(forged, candidate_rows[0]["boundary"],
                              candidate_rows[0]["relation_bits"])
        except AssertionError:
            forged_rejected = True
        assert forged_rejected
        assert block["adversarial"]["forged_candidate_rejected"] is True
    else:
        assert block["adversarial"]["forged_candidate_rejected"] is False
        forged_rejected = None
    return {"considered_nodes": block["considered_nodes"],
            "status_counts": block["status_counts"],
            "template_occurrences": [group["occurrences"] for group in block["template_groups"]],
            "forged_candidate_rejected": forged_rejected}


def main():
    artifact = json.loads((ROOT / "REPEATED_SUBDAG_TEMPLATES.json").read_text(encoding="utf-8"))
    small_summary = verify_block(artifact, expected_proof_nodes=65)
    assert small_summary["status_counts"] == {"FOUND": 16, "NO_COMPACT": 24, "UNKNOWN": 2}
    assert sorted(small_summary["template_occurrences"]) == [8, 8, 24]
    scale = artifact["scale_scan"]
    scale_summary = verify_block(scale, expected_proof_nodes=4097)
    assert scale_summary["considered_nodes"] == 2306
    assert scale_summary["status_counts"] == {"FOUND": 256, "NO_COMPACT": 1792, "UNKNOWN": 258}
    assert sorted(scale_summary["template_occurrences"]) == [256, 1792]
    cap = artifact["cap_sweep"]
    cap_summary = verify_block(cap, expected_proof_nodes=4097)
    assert cap_summary["considered_nodes"] == 2306
    assert cap_summary["status_counts"] == {"FOUND": 512, "NO_COMPACT": 1792, "UNKNOWN": 2}
    assert sorted(cap_summary["template_occurrences"]) == [256, 256, 1792]
    print(json.dumps({"independent_checks_passed": True,
                      "small": small_summary,
                      "scale": scale_summary,
                      "cap_sweep": cap_summary}))


if __name__ == "__main__":
    main()
