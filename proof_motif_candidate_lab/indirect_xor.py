"""Proof-carrying discovery of one-step hidden XOR relations.

Each local block is an exact three-variable parity CNF.  Two such equations
that share exactly one variable can be XORed to cancel that variable.  The
resulting relation is returned together with both local certificates; no
semantic equivalence oracle is used.
"""
from __future__ import annotations

from itertools import product

from miner import detect_parity_blocks, verify_parity_block


def detect_hidden_xor_pairs(clauses):
    """Find exact parity-block pairs with one cancelled variable."""
    blocks = detect_parity_blocks(clauses, arity=3)
    out = []
    for left_id, left in enumerate(blocks):
        left_support = set(left["support"])
        for right_id in range(left_id + 1, len(blocks)):
            right = blocks[right_id]
            right_support = set(right["support"])
            overlap = left_support & right_support
            if len(overlap) != 1:
                continue
            support = tuple(sorted(left_support ^ right_support))
            if len(support) != 4:
                continue
            candidate = {
                "kind": "HIDDEN_XOR_PAIR",
                "support": support,
                "rhs": int(left["rhs"]) ^ int(right["rhs"]),
                "block_ids": (left_id, right_id),
                "eliminated": next(iter(overlap)),
            }
            if verify_hidden_xor_pair(clauses, blocks, candidate):
                out.append(candidate)
    return out


def verify_hidden_xor_pair(clauses, blocks, candidate):
    """Independently check local certificates and the derived implication."""
    if candidate.get("kind") != "HIDDEN_XOR_PAIR":
        return False
    ids = tuple(candidate.get("block_ids", ()))
    if len(ids) != 2 or ids[0] >= ids[1]:
        return False
    if not all(0 <= index < len(blocks) for index in ids):
        return False
    left, right = (blocks[index] for index in ids)
    if not all(verify_parity_block(clauses, block) for block in (left, right)):
        return False
    overlap = set(left["support"]) & set(right["support"])
    support = tuple(sorted(set(left["support"]) ^ set(right["support"])))
    if len(overlap) != 1 or tuple(candidate["support"]) != support:
        return False
    if candidate["eliminated"] != next(iter(overlap)):
        return False
    rhs = int(left["rhs"]) ^ int(right["rhs"])
    if int(candidate["rhs"]) != rhs:
        return False

    # Exhaustive implication over the four visible variables is a small,
    # independent semantic check of the equation cancellation.
    union = tuple(sorted(set(left["support"]) | set(right["support"])))
    positions = {variable: index for index, variable in enumerate(union)}
    for bits in product((0, 1), repeat=len(union)):
        left_value = sum(bits[positions[v]] for v in left["support"]) & 1
        right_value = sum(bits[positions[v]] for v in right["support"]) & 1
        if left_value == int(left["rhs"]) and right_value == int(right["rhs"]):
            derived = sum(bits[positions[v]] for v in support) & 1
            if derived != rhs:
                return False
    return True

