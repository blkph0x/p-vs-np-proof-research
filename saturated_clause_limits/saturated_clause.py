"""Constructive paired-domain OR controls; exact support limits are proved separately."""
from pathlib import Path
import sys

MATCHING_SOURCE = Path(__file__).resolve().parent.parent / "matching_gadget_limits"
if str(MATCHING_SOURCE) not in sys.path:
    sys.path.insert(0, str(MATCHING_SOURCE))
from matching_boundary import (  # noqa: E402
    boundary_signature, encode_double_rail, even_delta_audit,
    threshold_support_audit, valid_domain, verify_matching,
)


def encoded_or(inputs):
    if type(inputs) is not int or inputs < 1:
        raise ValueError("OR must have at least one input")
    return [encode_double_rail(mask, inputs) for mask in range(1, 1 << inputs)]


def exact_or_exchange_witness(inputs):
    if type(inputs) is not int or inputs < 2:
        raise ValueError("the obstruction requires at least two inputs")
    feasible = set(encoded_or(inputs))
    A, B, e = 3, 12, 0
    neighbors = [{"f": f, "neighbor_A": A ^ 1 ^ (1 << f)} for f in (1, 2, 3)]
    assert A in feasible and B in feasible
    assert all(row["neighbor_A"] not in feasible for row in neighbors)
    return {"inputs": inputs, "A": A, "B": B, "e": e,
            "rejected_neighbors": neighbors, "violates_ordinary_exchange": True}


def raw_or_graph(inputs):
    if type(inputs) is not int or inputs < 1:
        raise ValueError("OR must have at least one input")
    return {"n": 2 * inputs, "terminals": list(range(2 * inputs)),
            "edges": [(2 * i, 2 * i + 1, 1) for i in range(inputs)]}


def saturated_or_graph(inputs):
    """Flat 0/1 OR costs only on the promised 00/11 domain; other states remain."""
    if type(inputs) is not int or inputs < 1:
        raise ValueError("OR must have at least one input")
    edges = [(2 * i, 2 * i + 1, 1) for i in range(inputs)]
    for j in range(inputs - 1):
        u, v = 2 * inputs + 2 * j, 2 * inputs + 2 * j + 1
        edges.append((u, v, 0))
        for i in range(inputs):
            edges.extend(((2 * i, u, 0), (2 * i + 1, v, 0)))
    return {"n": 4 * inputs - 2, "terminals": list(range(2 * inputs)), "edges": edges}


def signature_record(request):
    signature = boundary_signature(request["n"], request["edges"], request["terminals"])
    return [{"deleted": state, **value} for state, value in sorted(signature.items())]
