"""Exact recognition of compact four-clause ITE relations."""
from __future__ import annotations

from itertools import combinations, permutations, product


def _support(clause):
    variables = tuple(sorted(abs(literal) - 1 for literal in clause))
    return variables if len(set(variables)) == len(variables) else None


def _clause_true(clause, assignment):
    return any((literal > 0) == bool(assignment[abs(literal) - 1])
               for literal in clause)


def _candidate_groups(clauses):
    by_support = {}
    for index, clause in enumerate(clauses):
        if len(clause) != 3:
            continue
        support = _support(clause)
        if support is not None:
            by_support.setdefault(support, []).append(index)
    supports = sorted(by_support)
    groups = {}
    for left, right in combinations(supports, 2):
        union = tuple(sorted(set(left) | set(right)))
        if len(union) != 4:
            continue
        indices = tuple(sorted(index for support, values in by_support.items()
                              if set(support) <= set(union)
                              for index in values))
        if len(indices) == 4 and len(set(indices)) == 4:
            groups[(union, indices)] = indices
    return [(union, indices) for union, indices in groups]


def _valid_assignments(clauses, support):
    return {
        bits for bits in product((0, 1), repeat=4)
        if all(_clause_true(clauses[index],
                            {variable: bits[position]
                             for position, variable in enumerate(support)})
               for index in range(len(clauses)))
    }


def _ite_assignments(support, roles):
    z, c, a, b = roles
    positions = {variable: index for index, variable in enumerate(support)}
    return {
        bits for bits in product((0, 1), repeat=4)
        if bits[positions[z]] == (bits[positions[a]]
                                  if bits[positions[c]]
                                  else bits[positions[b]])
    }


def detect_compact_ite(clauses):
    """Find exact four-clause 3-CNF encodings of z = ite(c,a,b)."""
    out = []
    for support, indices in _candidate_groups(clauses):
        actual = _valid_assignments([clauses[index] for index in indices], support)
        for roles in permutations(support, 4):
            if actual != _ite_assignments(support, roles):
                continue
            candidate = {"kind": "COMPACT_ITE", "support": support,
                         "z": roles[0], "c": roles[1], "a": roles[2],
                         "b": roles[3], "clause_indices": indices}
            if verify_compact_ite(clauses, candidate):
                out.append(candidate)
    return out


def verify_compact_ite(clauses, candidate):
    if candidate.get("kind") != "COMPACT_ITE":
        return False
    support = tuple(candidate.get("support", ()))
    indices = tuple(candidate.get("clause_indices", ()))
    roles = (candidate.get("z"), candidate.get("c"), candidate.get("a"),
             candidate.get("b"))
    if (len(support) != 4 or len(set(support)) != 4 or len(indices) != 4
            or len(set(indices)) != 4):
        return False
    if set(roles) != set(support) or any(index < 0 or index >= len(clauses)
                                         for index in indices):
        return False
    actual = _valid_assignments([clauses[index] for index in indices], support)
    return actual == _ite_assignments(support, roles)
