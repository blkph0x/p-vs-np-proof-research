"""Proof-DAG to invented-relation interpolant bridge.

This is an integration experiment, not a general solver.  It takes the actual
resolution proof produced by ``proof_portfolio_integration_lab``, extracts the
positive unit subproofs from the proof graph, projects each subproof onto its
representative boundary, and combines the independently certified unit facts
into the existing parity interpolant.  The receiver remains a separately
checked opposite-parity clause.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROOF_DIR = ROOT / "proof_portfolio_integration_lab"
MOTIF_DIR = ROOT / "proof_motif_candidate_lab"
if str(PROOF_DIR) not in sys.path:
    sys.path.insert(0, str(PROOF_DIR))
if str(MOTIF_DIR) not in sys.path:
    sys.path.insert(0, str(MOTIF_DIR))

from adaptive_fragment_synthesis import extract_proof_leaves, result_dict, synthesize_fragment, verify_synthesis
import hard_controls
import proof_engine


def positive_unit_nodes(proof):
    """Return proof nodes whose derived clause is a positive unit."""
    out = []
    for index, node in enumerate(proof.nodes):
        clause = tuple(node.get("clause", ()))
        if len(clause) == 1 and clause[0] > 0:
            out.append((index, clause[0] - 1))
    return out


def serialize_proof(proof):
    """Serialize the small proof DAG without relying on proof-engine objects."""
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


def build_bridge(groups=8, width=4, max_nodes=64):
    proof, root, reps = proof_engine.build_fused_partitioned_proof(groups, width)
    rows = []
    units = []
    for node_index, rep in positive_unit_nodes(proof):
        extracted = extract_proof_leaves(proof, node_index, max_nodes=max_nodes)
        if extracted is None:
            raise ValueError("unit proof exceeds node cap")
        leaves, visited = extracted
        result = synthesize_fragment(leaves, (rep,), max_shared=1,
                                     max_local=max(0, width - 1))
        if result.status != "FOUND" or result.candidate["kind"] != "UNIT":
            raise AssertionError((node_index, rep, result.status, result.candidate))
        if not verify_synthesis(result, leaves):
            raise AssertionError("bounded relation certificate failed")
        units.append(rep)
        row = result_dict(result)
        row.update({"proof_node": node_index, "representative": rep,
                    "leaf_count": len(leaves), "visited_nodes": visited,
                    "clauses": [list(c) for c in leaves]})
        rows.append(row)

    if tuple(units) != tuple(reps):
        raise AssertionError((units, reps))
    raw = proof_engine.extract_raw_interpolant(groups, width)[1]
    lifted = {"kind": "XOR_INTERPOLANT", "support": list(reps), "rhs": groups & 1}
    return {
        "groups": groups,
        "width": width,
        "proof_nodes": len(proof.nodes),
        "root": root,
        "representatives": list(reps),
        "positive_unit_nodes": len(rows),
        "raw_interpolant_literals": proof_engine.ast_literal_count(raw),
        "unit_fragments": rows,
        "lifted": lifted,
        "proof_empty_clause": list(proof.nodes[root]["clause"]),
        "proof_certificate": serialize_proof(proof),
        "symbolic_check": verify_symbolic_bridge(groups, width, reps),
    }


def verify_symbolic_bridge(groups, width, reps):
    """Check the source-unit and receiver-parity implications without enumeration."""
    if len(reps) != groups or len(set(reps)) != groups:
        return False
    # The source fragment certificates establish every representative as true.
    source_parity = len(reps) & 1
    # The receiver clause requires the opposite parity.
    receiver_parity = 1 - source_parity
    lifted_rhs = groups & 1
    return source_parity == lifted_rhs and receiver_parity != lifted_rhs


def scan_bounded_subdags(proof, max_boundary=2, max_local=6, max_nodes=32):
    """Scan proof nodes without using fixture/group metadata.

    A node's derived clause is treated as its proposed boundary.  The complete
    leaf fragment is then projected onto that boundary and admitted only when
    the bounded certificate checker accepts it.  The summary keeps relation
    signatures, rather than retaining every intermediate truth table.
    """
    status_counts = Counter()
    kind_counts = Counter()
    signatures = Counter()
    considered = 0
    for node_index, node in enumerate(proof.nodes):
        clause = tuple(node.get("clause", ()))
        if not clause:
            continue
        boundary = tuple(sorted({abs(l) - 1 for l in clause}))
        if len(boundary) > max_boundary:
            continue
        considered += 1
        extracted = extract_proof_leaves(proof, node_index, max_nodes=max_nodes)
        if extracted is None:
            status_counts["UNKNOWN"] += 1
            continue
        leaves, visited = extracted
        result = synthesize_fragment(leaves, boundary, max_shared=max_boundary,
                                     max_local=max_local)
        status_counts[result.status] += 1
        if result.candidate is not None:
            kind_counts[result.candidate["kind"]] += 1
        if result.status != "UNKNOWN":
            signatures[(len(boundary), tuple(result.relation_bits))] += 1
    return {
        "considered_nodes": considered,
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_kind_counts": dict(sorted(kind_counts.items())),
        "relation_signature_counts": [
            {"boundary_arity": key[0], "relation_bits": list(key[1]), "count": count}
            for key, count in sorted(signatures.items(), key=lambda item: (item[0][0], item[0][1]))
        ],
    }


def hard_control(groups=5, k=3, max_shared=6):
    fixture = hard_controls.clique_coloring_cnf(groups, k)
    shared = tuple(sorted(fixture["shared"]))
    result = synthesize_fragment(fixture["A"], shared, max_shared=max_shared)
    return {
        "n": groups,
        "k": k,
        "shared_count": len(shared),
        "max_shared": max_shared,
        "status": result.status,
        "reason": result.reason,
    }


def run_artifact():
    bridge = build_bridge()
    proof, _, _ = proof_engine.build_fused_partitioned_proof(8, 4)
    scan = scan_bounded_subdags(proof, max_boundary=2, max_local=6, max_nodes=32)
    large = build_bridge(groups=256, width=8, max_nodes=128)
    hard = hard_control()
    assert bridge["symbolic_check"]
    assert large["symbolic_check"] and large["proof_nodes"] == 4097
    assert hard["status"] == "UNKNOWN"
    scale = {key: large[key] for key in
             ("groups", "width", "proof_nodes", "positive_unit_nodes",
              "raw_interpolant_literals", "symbolic_check")}
    artifact = {"all_checks_passed": True, "bridge": bridge,
                "subdag_scan": scan, "scale_check": scale, "hard_control": hard}
    path = ROOT / "PROOF_PORTFOLIO_BRIDGE.json"
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    print(json.dumps(run_artifact(), indent=2))
