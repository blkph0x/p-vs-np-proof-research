"""Certificate-backed prefix-threshold sequential cardinality counters.

The counter uses state variables q[i,j] with the intended meaning

    q[i,j] = 1  iff  x_1 + ... + x_i >= j.

Each state is defined by the exact recurrence

    q[i,j] = q[i-1,j] OR (x_i AND q[i-1,j-1]),

with q[i,0] permanently true and q[0,j] permanently false.  The final unit
not q[n,k+1] therefore expresses sum(x) <= k.  This is a small, explicit
sequential counter language; it is not claimed to recognize every published
cardinality encoding.

The role map is part of the certificate.  Reconstructing and checking the
clause set is polynomial in the supplied map.  A separate canonical-layout
scanner is deliberately capped and is not used to claim general discovery.
"""
from __future__ import annotations

from itertools import product

import networkx as nx


def normalize_clause(clause):
    values = {int(lit) for lit in clause}
    if 0 in values:
        raise ValueError("literal zero is not allowed")
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def _add_clause(target, terms):
    """Add a clause whose terms may include True/False constants."""
    if any(term is True for term in terms):
        return
    clause = normalize_clause(term for term in terms if term is not False)
    if clause is not None:
        target.add(clause)


def _validate_roles(inputs, states, n_inputs, threshold):
    if type(n_inputs) is not int or n_inputs < 1:
        raise ValueError("n_inputs must be positive")
    if type(threshold) is not int or threshold < 0 or threshold >= n_inputs:
        raise ValueError("threshold must satisfy 0 <= threshold < n_inputs")
    inputs = tuple(int(value) for value in inputs)
    if len(inputs) != n_inputs or len(set(inputs)) != n_inputs:
        raise ValueError("input role map is not a distinct n-tuple")
    states = tuple(tuple(int(value) for value in row) for row in states)
    if len(states) != n_inputs or any(len(row) != threshold + 1 for row in states):
        raise ValueError("state role map has the wrong dimensions")
    flat = tuple(value for row in states for value in row)
    if len(set(flat)) != len(flat) or set(flat) & set(inputs):
        raise ValueError("state and input roles overlap")
    if min(inputs + flat, default=-1) < 0:
        raise ValueError("variable ids must be nonnegative")
    return inputs, states


def canonical_roles(n_inputs, threshold):
    inputs = tuple(range(n_inputs))
    start = n_inputs
    states = tuple(
        tuple(start + (i - 1) * (threshold + 1) + (j - 1)
              for j in range(1, threshold + 2))
        for i in range(1, n_inputs + 1)
    )
    return inputs, states


def expected_clauses(n_inputs, threshold, inputs=None, states=None):
    """Reconstruct the exact CNF for a supplied role map."""
    if inputs is None or states is None:
        inputs, states = canonical_roles(n_inputs, threshold)
    inputs, states = _validate_roles(inputs, states, n_inputs, threshold)
    clauses = set()
    for i in range(1, n_inputs + 1):
        x = inputs[i - 1]
        for j in range(1, threshold + 2):
            q = states[i - 1][j - 1]
            previous_j = states[i - 2][j - 1] if i >= 2 else False
            previous_jm1 = True if j == 1 else (states[i - 2][j - 2] if i >= 2 else False)

            # q -> previous_j OR (x AND previous_jm1), split by the two
            # disjuncts; and each disjunct -> q.
            if previous_j is not False:
                _add_clause(clauses, [-(previous_j + 1), q + 1])
            if previous_jm1 is True:
                _add_clause(clauses, [-(x + 1), q + 1])
            elif previous_jm1 is False:
                # x AND False is false, so this implication is tautological.
                pass
            else:
                _add_clause(clauses, [-(x + 1), -(previous_jm1 + 1), q + 1])

            _add_clause(clauses, [-(q + 1), False if previous_j is False else previous_j + 1, x + 1])
            if previous_jm1 is True:
                # q -> A OR True is tautological.
                pass
            elif previous_jm1 is False:
                _add_clause(clauses, [-(q + 1), False if previous_j is False else previous_j + 1])
            else:
                _add_clause(clauses, [-(q + 1), False if previous_j is False else previous_j + 1,
                                       previous_jm1 + 1])
    clauses.add((-(states[-1][-1] + 1),))
    return tuple(sorted(clauses))


def certificate(n_inputs, threshold, inputs=None, states=None):
    if inputs is None or states is None:
        inputs, states = canonical_roles(n_inputs, threshold)
    inputs, states = _validate_roles(inputs, states, n_inputs, threshold)
    variables = inputs + tuple(value for row in states for value in row)
    return {
        "kind": "PREFIX_THRESHOLD_COUNTER",
        "n_inputs": n_inputs,
        "threshold": threshold,
        "inputs": list(inputs),
        "states": [list(row) for row in states],
        "output_state": states[-1][-1],
        "variable_count": max(variables) + 1,
    }


def _certificate_roles(cert):
    if cert.get("kind") != "PREFIX_THRESHOLD_COUNTER":
        raise ValueError("wrong certificate kind")
    n_inputs = cert.get("n_inputs")
    threshold = cert.get("threshold")
    inputs = cert.get("inputs")
    states = cert.get("states")
    return n_inputs, threshold, *_validate_roles(inputs, states, n_inputs, threshold)


def full_projection(clauses, cert, max_total_variables=20):
    """Enumerate all variables for a small exact projection oracle.

    The oracle returns UNKNOWN_CAP rather than silently sampling when the
    full assignment universe exceeds the explicit budget.
    """
    n_inputs, threshold, inputs, states = _certificate_roles(cert)
    state_ids = tuple(value for row in states for value in row)
    variables = tuple(inputs) + state_ids
    if len(variables) > max_total_variables:
        return {"status": "UNKNOWN_CAP", "total_variables": len(variables)}
    normalized = tuple(normalize_clause(clause) for clause in clauses)
    normalized = tuple(clause for clause in normalized if clause is not None)
    accepted = set()
    for bits in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if all(any((literal > 0) == assignment[abs(literal) - 1]
                   for literal in clause)
               for clause in normalized):
            accepted.add(tuple(int(assignment[value]) for value in inputs))
    expected = {
        bits for bits in product((0, 1), repeat=n_inputs)
        if sum(bits) <= threshold
    }
    return {
        "status": "PASS" if accepted == expected else "FAIL",
        "total_variables": len(variables),
        "accepted_inputs": sorted(accepted),
        "expected_inputs": sorted(expected),
    }


def verify_certificate(clauses, cert, semantic_cap=20):
    """Return a detailed structural/semantic verification record."""
    try:
        n_inputs, threshold, inputs, states = _certificate_roles(cert)
        expected = expected_clauses(n_inputs, threshold, inputs, states)
    except (KeyError, TypeError, ValueError):
        return {"status": "REJECT", "reason": "malformed certificate"}
    try:
        actual = tuple(sorted(normalize_clause(clause) for clause in clauses
                              if normalize_clause(clause) is not None))
    except (TypeError, ValueError):
        return {"status": "REJECT", "reason": "malformed clause input"}
    if actual != expected:
        return {"status": "REJECT", "reason": "clause set does not match counter"}
    semantic = full_projection(actual, cert, max_total_variables=semantic_cap)
    if semantic["status"] == "FAIL":
        return {"status": "REJECT", "reason": "projection is not at-most-k", "semantic": semantic}
    if semantic["status"] == "UNKNOWN_CAP":
        return {"status": "ACCEPT_STRUCTURAL_UNKNOWN_SEMANTIC", "semantic": semantic}
    return {"status": "ACCEPT", "semantic": semantic}


def discover_canonical(clauses, max_inputs=8, max_threshold=7, max_candidates=64):
    """Try canonical layouts under a finite candidate budget.

    This is intentionally only a bounded scanner.  It does not enumerate role
    permutations and therefore cannot be used as a universal recognizer.
    """
    candidates = 0
    for n_inputs in range(1, max_inputs + 1):
        for threshold in range(min(max_threshold, n_inputs - 1) + 1):
            candidates += 1
            if candidates > max_candidates:
                return {"status": "UNKNOWN_CAP", "candidates": candidates - 1}
            cert = certificate(n_inputs, threshold)
            result = verify_certificate(clauses, cert)
            if result["status"] in {"ACCEPT", "ACCEPT_STRUCTURAL_UNKNOWN_SEMANTIC"}:
                return {"status": "FOUND", "candidates": candidates, "certificate": cert,
                        "verification": result}
    return {"status": "NOT_FOUND", "candidates": candidates}


def _incidence_graph(clauses):
    graph = nx.Graph()
    normalized = tuple(sorted(normalize_clause(clause) for clause in clauses
                              if normalize_clause(clause) is not None))
    variables = sorted({abs(literal) - 1 for clause in normalized for literal in clause})
    for variable in variables:
        graph.add_node(("v", variable), kind="variable", width=None)
    for index, clause in enumerate(normalized):
        node = ("c", index)
        graph.add_node(node, kind="clause", width=len(clause))
        for literal in clause:
            graph.add_edge(("v", abs(literal) - 1), node,
                           sign=1 if literal > 0 else -1)
    return graph


def discover_isomorphic(clauses, n_inputs, threshold, *, max_variables=24,
                        max_isomorphisms=64):
    """Discover a role map through bounded signed incidence-graph isomorphism.

    The exact counter shape is the target graph. This search is a bounded
    structural proposal, not a universal polynomial role-discovery theorem.
    Certificate validation remains the authority.
    """
    try:
        actual = tuple(sorted(normalize_clause(clause) for clause in clauses
                              if normalize_clause(clause) is not None))
        target = expected_clauses(n_inputs, threshold)
        actual_variables = {abs(literal) - 1 for clause in actual for literal in clause}
        if len(actual_variables) > max_variables:
            return {"status": "UNKNOWN_CAP", "reason": "variable cap exceeded",
                    "variables": len(actual_variables), "embeddings": 0}
        if len(actual) != len(target):
            return {"status": "NOT_FOUND", "embeddings": 0}
        source_graph = _incidence_graph(target)
        actual_graph = _incidence_graph(actual)
        node_match = lambda left, right: (
            left.get("kind") == right.get("kind")
            and left.get("width") == right.get("width")
        )
        edge_match = lambda left, right: left.get("sign") == right.get("sign")
        matcher = nx.algorithms.isomorphism.GraphMatcher(
            source_graph, actual_graph, node_match=node_match, edge_match=edge_match
        )
        embeddings = 0
        canonical_inputs, canonical_states = canonical_roles(n_inputs, threshold)
        for mapping in matcher.isomorphisms_iter():
            embeddings += 1
            if embeddings > max_isomorphisms:
                return {"status": "UNKNOWN_CAP", "reason": "embedding cap exceeded",
                        "variables": len(actual_variables), "embeddings": embeddings - 1}
            inputs = tuple(mapping[("v", variable)][1] for variable in canonical_inputs)
            states = tuple(tuple(mapping[("v", variable)][1] for variable in row)
                           for row in canonical_states)
            candidate = certificate(n_inputs, threshold, inputs, states)
            verification = verify_certificate(actual, candidate)
            if verification["status"] in {"ACCEPT", "ACCEPT_STRUCTURAL_UNKNOWN_SEMANTIC"}:
                return {"status": "FOUND", "embeddings": embeddings,
                        "certificate": candidate, "verification": verification}
        return {"status": "NOT_FOUND", "embeddings": embeddings}
    except (KeyError, TypeError, ValueError, nx.NetworkXError):
        return {"status": "NOT_FOUND", "embeddings": 0}
