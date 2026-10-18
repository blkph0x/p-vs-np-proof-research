"""Bounded proof-carrying closure for chains of exact XOR3 blocks."""
from __future__ import annotations

from miner import detect_parity_blocks, verify_parity_block


def _as_relation(block_id, block):
    return {"support": tuple(block["support"]), "rhs": int(block["rhs"]),
            "proof_blocks": (block_id,), "depth": 0}


def _key(relation):
    return tuple(relation["support"]), int(relation["rhs"]) & 1


def _combine(left, right, max_support):
    overlap = set(left["support"]) & set(right["support"])
    if len(overlap) != 1:
        return None
    support = tuple(sorted(set(left["support"]) ^ set(right["support"])))
    if not support or len(support) > max_support:
        return None
    proof = tuple(sorted(set(left["proof_blocks"]) ^ set(right["proof_blocks"])))
    if not proof:
        return None
    return {"support": support, "rhs": int(left["rhs"]) ^ int(right["rhs"]),
            "proof_blocks": proof, "depth": max(left["depth"], right["depth"]) + 1}


def verify_relation(clauses, blocks, relation):
    """Recompute the GF(2) row and all local source certificates."""
    proof = tuple(relation["proof_blocks"])
    if not proof or len(set(proof)) != len(proof):
        return False
    support = set()
    rhs = 0
    for block_id in proof:
        if not (0 <= block_id < len(blocks)):
            return False
        block = blocks[block_id]
        if not verify_parity_block(clauses, block):
            return False
        support ^= set(block["support"])
        rhs ^= int(block["rhs"])
    return (tuple(sorted(support)) == tuple(relation["support"])
            and rhs == (int(relation["rhs"]) & 1))


def _json_relation(relation):
    return {"support": list(relation["support"]), "rhs": int(relation["rhs"]) & 1,
            "proof_blocks": list(relation["proof_blocks"]),
            "depth": int(relation["depth"])}


def bounded_closure(clauses, max_rounds=4, max_support=8, max_relations=4096):
    """Join one-overlap equations, stopping explicitly at a relation cap."""
    blocks = detect_parity_blocks(clauses, arity=3)
    known = {}
    for block_id, block in enumerate(blocks):
        relation = _as_relation(block_id, block)
        known[_key(relation)] = relation
    frontier = list(known.values())
    frontier_counts = [len(frontier)]
    for _round in range(1, max_rounds + 1):
        additions = {}
        snapshot = list(known.values())
        for left in frontier:
            for right in snapshot:
                candidate = _combine(left, right, max_support)
                if candidate is None:
                    continue
                key = _key(candidate)
                if key in known or key in additions:
                    continue
                additions[key] = candidate
                if len(additions) > max_relations:
                    return {
                        "status": "UNKNOWN_CAP",
                        "blocks": [{"support": list(block["support"]),
                                    "rhs": block["rhs"],
                                    "clause_indices": list(block["clause_indices"])}
                                   for block in blocks],
                        "relations": [], "frontier_counts": frontier_counts,
                        "rounds_completed": _round - 1,
                        "cap": {"max_rounds": max_rounds,
                                "max_support": max_support,
                                "max_relations": max_relations},
                    }
        if not additions:
            break
        known.update(additions)
        frontier = list(additions.values())
        frontier_counts.append(len(frontier))
    relations = [_json_relation(known[key]) for key in sorted(known)]
    return {
        "status": "BOUNDED_COMPLETE",
        "blocks": [{"support": list(block["support"]),
                    "rhs": block["rhs"],
                    "clause_indices": list(block["clause_indices"])}
                   for block in blocks],
        "relations": relations,
        "frontier_counts": frontier_counts,
        "rounds_completed": len(frontier_counts) - 1,
        "cap": {"max_rounds": max_rounds, "max_support": max_support,
                "max_relations": max_relations},
    }

