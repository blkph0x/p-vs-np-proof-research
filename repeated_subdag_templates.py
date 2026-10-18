"""Bounded discovery and reuse of repeated proof-DAG relation templates.

This experiment removes the known group labels from the small fused proof.  It
scans every nonempty derived clause whose proposed boundary is at most two
variables, projects the complete leaf sub-DAG, and asks the bounded relation
synthesizer for a certificate.  Candidates are canonicalized by boundary
position, so repeated local shapes can be counted without treating variable
names as semantic evidence.

Reuse is deliberately charged.  Every occurrence still pays its exact
projection work.  Only the fixed candidate-vocabulary search is amortized after
the first occurrence, and the artifact records both naive and reused work.
This is a finite proof-DAG experiment, not a claim that arbitrary proofs have
small interfaces or that semantic equality can be discovered in polynomial
time.
"""

from __future__ import annotations

from collections import Counter, OrderedDict
import copy
import json
from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROOF_DIR = ROOT / "proof_portfolio_integration_lab"
if str(PROOF_DIR) not in sys.path:
    sys.path.insert(0, str(PROOF_DIR))

from adaptive_fragment_synthesis import (  # noqa: E402
    extract_proof_leaves,
    synthesize_fragment,
    verify_synthesis,
)
import proof_engine  # noqa: E402


def serialize_proof(proof):
    """Serialize the proof without retaining proof-engine objects."""
    nodes = []
    for node in proof.nodes:
        row = {"clause": list(node["clause"])}
        if "part" in node:
            row["part"] = node["part"]
        else:
            row.update({"left": node["left"], "right": node["right"],
                        "pivot": node["pivot"]})
        nodes.append(row)
    return {"A": [list(c) for c in proof.A], "B": [list(c) for c in proof.B],
            "nodes": nodes}


def boundary_for_clause(clause):
    return tuple(sorted({abs(int(lit)) - 1 for lit in clause}))


def candidate_value(candidate, assignment):
    kind = candidate["kind"]
    if kind == "UNIT":
        return bool(assignment[candidate["var"]]) == bool(candidate["value"])
    if kind == "XOR":
        return (sum(assignment[v] for v in candidate["support"]) & 1) == int(candidate["rhs"])
    if kind == "PB":
        lhs = sum(int(w) * int(assignment[int(v)])
                  for v, w in candidate["weights"].items())
        return lhs <= int(candidate["bound"]) if candidate["sense"] == "<=" else lhs >= int(candidate["bound"])
    if kind == "ITE":
        expected = assignment[candidate["a"]] if assignment[candidate["c"]] else assignment[candidate["b"]]
        return bool(assignment[candidate["z"]]) == bool(expected)
    if kind == "TRUTH_TABLE":
        index = 0
        for variable in candidate["support"]:
            index = (index << 1) | int(bool(assignment[variable]))
        return bool((int(candidate["accepted_mask"]) >> index) & 1)
    raise ValueError(kind)


def candidate_matches_relation(candidate, shared, relation_bits):
    for bits, expected in zip(product((False, True), repeat=len(shared)), relation_bits):
        assignment = dict(zip(shared, bits))
        if int(candidate_value(candidate, assignment)) != int(expected):
            return False
    return True


def canonical_candidate(candidate, shared):
    """Rename interface variables to their sorted boundary positions."""
    positions = {int(variable): index for index, variable in enumerate(shared)}
    kind = candidate["kind"]
    if kind == "UNIT":
        return {"kind": kind, "var": positions[int(candidate["var"])],
                "value": bool(candidate["value"])}
    if kind == "XOR":
        return {"kind": kind,
                "support": [positions[int(variable)] for variable in candidate["support"]],
                "rhs": int(candidate["rhs"])}
    if kind == "PB":
        weights = {str(positions[int(variable)]): int(weight)
                   for variable, weight in candidate["weights"].items()}
        return {"kind": kind, "weights": dict(sorted(weights.items(), key=lambda item: int(item[0]))),
                "sense": candidate["sense"], "bound": int(candidate["bound"])}
    if kind == "ITE":
        return {"kind": kind,
                "z": positions[int(candidate["z"])],
                "c": positions[int(candidate["c"])],
                "a": positions[int(candidate["a"])],
                "b": positions[int(candidate["b"])]}
    if kind == "TRUTH_TABLE":
        return {"kind": kind,
                "support": [positions[int(variable)] for variable in candidate["support"]],
                "accepted_mask": int(candidate["accepted_mask"])}
    raise ValueError(kind)


def fixed_candidate_search_work(shared_count, max_truth_table_bits=12):
    """Match adaptive_fragment_synthesis' bounded vocabulary accounting."""
    n = int(shared_count)
    candidate_count = 2 * n
    candidate_count += 2 * ((1 << n) - 1)
    candidate_count += 2 * (n + 1)
    if n == 4:
        candidate_count += 24
    if n <= max_truth_table_bits:
        candidate_count += 1
    return (1 << n) * candidate_count


def work_accounting(clauses, result):
    projection = (1 << (len(result.shared) + len(result.local))) * max(1, len(clauses))
    search = fixed_candidate_search_work(len(result.shared))
    if result.discovery_work != projection + search:
        raise AssertionError((result.discovery_work, projection, search))
    return {"projection_work": projection,
            "candidate_search_work": search,
            "template_check_work": 1 << len(result.shared),
            "naive_work": result.discovery_work}


def template_signature(row):
    return json.dumps({"status": row["status"],
                       "candidate": row["canonical_candidate"],
                       "relation_bits": row["relation_bits"]}, sort_keys=True)


def _row_from_result(proof, node_index, clause, boundary, leaves, visited, result):
    if not verify_synthesis(result, leaves):
        raise AssertionError((node_index, "relation certificate failed"))
    candidate = result.candidate
    row = {
        "node_index": int(node_index),
        "clause": list(clause),
        "boundary": list(boundary),
        "status": result.status,
        "candidate": candidate,
        "candidates": list(result.all_candidates),
        "relation_bits": list(result.relation_bits),
        "local": list(result.local),
        "leaf_clauses": [list(c) for c in leaves],
        "visited_nodes": int(visited),
        "reason": result.reason,
    }
    accounting = work_accounting(leaves, result)
    row.update(accounting)
    row["canonical_candidate"] = canonical_candidate(candidate, boundary) if candidate is not None else None
    row["template_key"] = template_signature(row) if candidate is not None else None
    return row


def _unknown_row(node_index, clause, boundary, reason, *, leaves=(), visited=None,
                 local=(), stage="subdag_cap"):
    return {
        "node_index": int(node_index),
        "clause": list(clause),
        "boundary": list(boundary),
        "status": "UNKNOWN",
        "candidate": None,
        "candidates": [],
        "relation_bits": [],
        "local": list(local),
        "leaf_clauses": [list(c) for c in leaves],
        "visited_nodes": visited,
        "reason": reason,
        "unknown_stage": stage,
        "projection_work": 0,
        "candidate_search_work": 0,
        "template_check_work": 0,
        "naive_work": 0,
        "canonical_candidate": None,
        "template_key": None,
    }


def scan_repeated_templates(groups=8, width=4, max_boundary=2,
                            max_local=6, max_nodes=32):
    proof, root, representatives = proof_engine.build_fused_partitioned_proof(groups, width)
    records = []
    for node_index, node in enumerate(proof.nodes):
        clause = tuple(node.get("clause", ()))
        if not clause:
            continue
        boundary = boundary_for_clause(clause)
        if len(boundary) > max_boundary:
            continue
        extracted = extract_proof_leaves(proof, node_index, max_nodes=max_nodes)
        if extracted is None:
            records.append(_unknown_row(node_index, clause, boundary,
                                        "proof sub-DAG exceeds node cap"))
            continue
        leaves, visited = extracted
        result = synthesize_fragment(leaves, boundary, max_shared=max_boundary,
                                     max_local=max_local)
        if result.status == "UNKNOWN":
            records.append(_unknown_row(node_index, clause, boundary,
                                        result.reason, leaves=leaves,
                                        visited=visited, local=result.local,
                                        stage="projection_cap"))
            continue
        records.append(_row_from_result(proof, node_index, clause, boundary,
                                         leaves, visited, result))

    groups_by_key = OrderedDict()
    for row in records:
        if row["template_key"] is None:
            continue
        groups_by_key.setdefault(row["template_key"], []).append(row)
    template_groups = []
    for template_id, (key, rows) in enumerate(groups_by_key.items()):
        for row in rows:
            row["template_id"] = f"T{template_id}"
        first = rows[0]
        naive = sum(row["naive_work"] for row in rows)
        reused = first["naive_work"] + sum(
            row["projection_work"] + row["template_check_work"] for row in rows[1:])
        template_groups.append({
            "template_id": f"T{template_id}",
            "template_key": key,
            "status": first["status"],
            "canonical_candidate": first["canonical_candidate"],
            "relation_bits": first["relation_bits"],
            "occurrences": len(rows),
            "proof_nodes": [row["node_index"] for row in rows],
            "naive_work": naive,
            "reused_work": reused,
            "saved_work": naive - reused,
        })

    status_counts = Counter(row["status"] for row in records)
    candidate_kind_counts = Counter(row["candidate"]["kind"] for row in records
                                    if row["candidate"] is not None)
    artifact = {
        "all_checks_passed": True,
        "parameters": {"groups": groups, "width": width,
                       "max_boundary": max_boundary, "max_local": max_local,
                       "max_nodes": max_nodes},
        "proof_nodes": len(proof.nodes),
        "proof_root": root,
        "representatives": list(representatives),
        "proof_certificate": serialize_proof(proof),
        "considered_nodes": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_kind_counts": dict(sorted(candidate_kind_counts.items())),
        "records": records,
        "template_groups": template_groups,
        "adversarial": {"forged_candidate_rejected": False},
    }
    for row in records:
        if row["candidate"] is not None:
            forged = copy.deepcopy(row["candidate"])
            if forged["kind"] == "UNIT":
                forged["value"] = not bool(forged["value"])
            elif forged["kind"] == "PB":
                forged["bound"] = int(forged["bound"]) + (1 if forged["sense"] == ">=" else -1)
            elif forged["kind"] == "XOR":
                forged["rhs"] = 1 - int(forged["rhs"])
            elif forged["kind"] == "TRUTH_TABLE":
                forged["accepted_mask"] = int(forged["accepted_mask"]) ^ 1
            else:
                forged["z"], forged["a"] = forged["a"], forged["z"]
            artifact["adversarial"]["forged_candidate_rejected"] = not candidate_matches_relation(
                forged, row["boundary"], row["relation_bits"])
            break
    if not artifact["adversarial"]["forged_candidate_rejected"]:
        raise AssertionError("adversarial candidate mutation was accepted")
    if (groups, width, max_boundary, max_local, max_nodes) == (8, 4, 2, 6, 32):
        if artifact["status_counts"] != {"FOUND": 16, "NO_COMPACT": 24, "UNKNOWN": 2}:
            raise AssertionError(artifact["status_counts"])
        if artifact["candidate_kind_counts"] != {"PB": 8, "TRUTH_TABLE": 24, "UNIT": 8}:
            raise AssertionError(artifact["candidate_kind_counts"])
        if sorted(group["occurrences"] for group in template_groups) != [8, 8, 24]:
            raise AssertionError(template_groups)
    return artifact


def write_artifact():
    artifact = scan_repeated_templates()
    # Retain the larger scan in the same serialized artifact so an independent
    # checker can replay it rather than trusting a producer-only summary.
    artifact["scale_scan"] = scan_repeated_templates(
        groups=256, width=8, max_boundary=2, max_local=6, max_nodes=32)
    artifact["cap_sweep"] = scan_repeated_templates(
        groups=256, width=8, max_boundary=2, max_local=7, max_nodes=32)
    (ROOT / "REPEATED_SUBDAG_TEMPLATES.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    print(json.dumps(write_artifact(), indent=2))
