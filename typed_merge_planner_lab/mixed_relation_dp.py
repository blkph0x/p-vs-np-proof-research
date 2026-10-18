"""Proof-producing frontier DP for arbitrary finite Boolean relations."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Constraint:
    scope: tuple[int, ...]
    relation: frozenset[tuple[int, ...]]


def _validate(n: int, constraints: tuple[Constraint, ...], order: tuple[int, ...]) -> None:
    if n < 0 or tuple(sorted(order)) != tuple(range(n)):
        raise ValueError("order must be a permutation of the variables")
    for c in constraints:
        if len(set(c.scope)) != len(c.scope):
            raise ValueError("constraint scope repeats a variable")
        if any(v < 0 or v >= n for v in c.scope):
            raise ValueError("constraint variable outside range")
        if any(len(row) != len(c.scope) or any(bit not in (0, 1) for bit in row)
               for row in c.relation):
            raise ValueError("relation tuple has the wrong Boolean shape")


def _boundary(n: int, constraints: tuple[Constraint, ...], order: tuple[int, ...], cut: int) -> tuple[int, ...]:
    pos = {v: i for i, v in enumerate(order)}
    return tuple(v for v in order[:cut]
                 if any(v in c.scope and any(pos[u] >= cut for u in c.scope)
                        for c in constraints))


def solve(n: int, constraints: tuple[Constraint, ...], order: tuple[int, ...]) -> dict[str, object]:
    """Return an exact SAT result and a replayable cut-by-cut certificate."""
    _validate(n, constraints, order)
    pos = {v: i for i, v in enumerate(order)}
    last = [max((pos[v] for v in c.scope), default=-1) for c in constraints]
    for c, end in zip(constraints, last):
        if end == -1 and () not in c.relation:
            return {"status": "UNSAT", "sat": False, "max_width": 0,
                    "certificate": {"n": n, "order": list(order), "cuts": [],
                                     "empty_constraint": True}}
    boundaries = [_boundary(n, constraints, order, cut) for cut in range(n + 1)]
    states: list[tuple[int, ...]] = [()]
    cuts = [{"boundary": list(boundaries[0]), "states": [list(s) for s in states],
             "transitions": []}]
    max_states = 1
    for cut, variable in enumerate(order):
        old_boundary = boundaries[cut]
        new_boundary = boundaries[cut + 1]
        old_index = {state: i for i, state in enumerate(states)}
        candidates: list[tuple[int, int, tuple[int, ...]]] = []
        for state_index, state in enumerate(states):
            assignment = dict(zip(old_boundary, state))
            for bit in (0, 1):
                assignment[variable] = bit
                accepted = True
                for c, end in zip(constraints, last):
                    if end != cut:
                        continue
                    row = tuple(assignment[v] for v in c.scope)
                    if row not in c.relation:
                        accepted = False
                        break
                if accepted:
                    new_state = tuple(assignment[v] for v in new_boundary)
                    candidates.append((state_index, bit, new_state))
        unique = sorted({row[2] for row in candidates})
        new_index = {state: i for i, state in enumerate(unique)}
        transitions = [{"from": old, "bit": bit, "to": new_index[state]}
                       for old, bit, state in candidates]
        states = unique
        max_states = max(max_states, len(states))
        cuts.append({"boundary": list(new_boundary),
                     "states": [list(s) for s in states],
                     "transitions": transitions})
    sat = bool(states and states == [()])
    certificate = {"n": n, "order": list(order),
                   "constraints": [{"scope": list(c.scope),
                                    "relation": [list(row) for row in sorted(c.relation)]}
                                   for c in constraints],
                   "cuts": cuts, "sat": sat, "max_width": max(map(len, boundaries), default=0),
                   "max_states": max_states}
    return {"status": "SAT" if sat else "UNSAT", "sat": sat,
            "max_width": certificate["max_width"], "max_states": max_states,
            "certificate": certificate}


def source_hashes() -> dict[str, str]:
    names = ("mixed_relation_dp.py", "run_mixed_relation_dp.py",
             "MIXED_RELATION_DP_THEOREM.md", "MIXED_RELATION_DP_REVIEW.py",
             "test_mixed_relation_dp.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
