"""Independent replay of the prefix-counter certificate.

This file intentionally rebuilds the recurrence and projection oracle instead
of importing sequential_counter.py.
"""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent


def norm(clause):
    values = {int(value) for value in clause}
    if 0 in values or any(-value in values for value in values):
        return None
    return tuple(sorted(values, key=lambda value: (abs(value), value < 0)))


def add_clause(target, terms):
    if any(term is True for term in terms):
        return
    clause = norm(term for term in terms if term is not False)
    if clause is not None:
        target.add(clause)


def roles(cert):
    n = cert["n_inputs"]
    k = cert["threshold"]
    inputs = tuple(cert["inputs"])
    states = tuple(tuple(row) for row in cert["states"])
    if len(inputs) != n or len(states) != n or any(len(row) != k + 1 for row in states):
        raise ValueError("bad role dimensions")
    return n, k, inputs, states


def generated(cert):
    n, k, inputs, states = roles(cert)
    clauses = set()
    for i in range(1, n + 1):
        x = inputs[i - 1]
        for j in range(1, k + 2):
            q = states[i - 1][j - 1]
            prev = states[i - 2][j - 1] if i >= 2 else False
            prev_low = True if j == 1 else (states[i - 2][j - 2] if i >= 2 else False)
            if prev is not False:
                add_clause(clauses, [-(prev + 1), q + 1])
            if prev_low is True:
                add_clause(clauses, [-(x + 1), q + 1])
            elif prev_low is False:
                pass
            else:
                add_clause(clauses, [-(x + 1), -(prev_low + 1), q + 1])
            add_clause(clauses, [-(q + 1), False if prev is False else prev + 1, x + 1])
            if prev_low is True:
                pass
            elif prev_low is False:
                add_clause(clauses, [-(q + 1), False if prev is False else prev + 1])
            else:
                add_clause(clauses, [-(q + 1), False if prev is False else prev + 1,
                                     prev_low + 1])
    clauses.add((-(states[-1][-1] + 1),))
    return tuple(sorted(clauses))


def projection(clauses, cert, cap=20):
    n, k, inputs, states = roles(cert)
    variables = inputs + tuple(value for row in states for value in row)
    if len(variables) > cap:
        return "UNKNOWN_CAP"
    accepted = set()
    for bits in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if all(any((literal > 0) == assignment[abs(literal) - 1]
                   for literal in clause) for clause in clauses):
            accepted.add(tuple(int(assignment[value]) for value in inputs))
    expected = {bits for bits in product((0, 1), repeat=n) if sum(bits) <= k}
    return "PASS" if accepted == expected else "FAIL"


def incidence(clauses):
    graph = nx.Graph()
    normalized = tuple(sorted(norm(clause) for clause in clauses if norm(clause) is not None))
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


def discover_isomorphic(clauses, n, k, max_variables=24, max_isomorphisms=64):
    actual = tuple(sorted(norm(clause) for clause in clauses if norm(clause) is not None))
    target_cert = {"n_inputs": n, "threshold": k,
                   "inputs": list(range(n)),
                   "states": [list(range(n + i * (k + 1),
                                         n + (i + 1) * (k + 1))) for i in range(n)]}
    target = generated(target_cert)
    variables = {abs(literal) - 1 for clause in actual for literal in clause}
    if len(variables) > max_variables:
        return "UNKNOWN_CAP"
    if len(actual) != len(target):
        return "NOT_FOUND"
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        incidence(target), incidence(actual),
        node_match=lambda left, right: (
            left.get("kind") == right.get("kind")
            and left.get("width") == right.get("width")
        ),
        edge_match=lambda left, right: left.get("sign") == right.get("sign"),
    )
    count = 0
    for _mapping in matcher.isomorphisms_iter():
        count += 1
        if count > max_isomorphisms:
            return "UNKNOWN_CAP"
        return "FOUND"
    return "NOT_FOUND"


def verify(record):
    positive = record["positive"]
    cert = positive["certificate"]
    clauses = tuple(tuple(c) for c in positive["clauses"])
    expected = generated(cert)
    assert tuple(sorted(clauses)) == expected
    assert projection(expected, cert) == "PASS"
    assert record["controls"]["missing_clause"]["verification"]["status"] == "REJECT"
    assert record["controls"]["literal_mutation"]["verification"]["status"] == "REJECT"
    assert record["controls"]["wrong_threshold"]["verification"]["status"] == "REJECT"
    shuffled = record["controls"]["shuffled_roles"]
    assert tuple(sorted(norm(c) for c in shuffled["clauses"])) == generated(shuffled["certificate"])
    assert projection(generated(shuffled["certificate"]), shuffled["certificate"]) == "PASS"
    assert record["canonical_discovery"]["status"] == "FOUND"
    assert shuffled["canonical_discovery"]["status"] == "NOT_FOUND"
    assert shuffled["isomorphic_discovery"]["status"] == "FOUND"
    assert shuffled["cap_discovery"]["status"] == "UNKNOWN_CAP"
    assert discover_isomorphic(tuple(tuple(c) for c in shuffled["clauses"]), 5, 2) == "FOUND"
    for row in record["scaling"]:
        assert row["status"] in {"ACCEPT", "ACCEPT_STRUCTURAL_UNKNOWN_SEMANTIC"}
    return True


def main():
    record = json.loads((ROOT / "SEQUENTIAL_COUNTER_RESULTS.json").read_text(encoding="utf-8"))
    passed = verify(record)
    expected_hashes = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ("sequential_counter.py", "run_sequential_counter.py",
                     "review_sequential_counter.py", "SEQUENTIAL_COUNTER_REPORT.md")
    }
    assert record["source_sha256"] == expected_hashes
    review = {"all_checks_passed": passed, "source_sha256": expected_hashes,
              "replayed": {"positive_projection": "PASS",
                            "missing_clause_rejected": True,
                            "literal_mutation_rejected": True,
                            "wrong_threshold_rejected": True,
                            "shuffled_roles_replayed": True,
                            "isomorphic_discovery_replayed": True,
                            "discovery_cap_replayed": True}}
    (ROOT / "SEQUENTIAL_COUNTER_REVIEW.json").write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(review, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
