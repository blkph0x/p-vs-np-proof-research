"""Proof-producing solver for a supplied Schaefer backdoor.

The solver is deliberately parameterized.  A backdoor B is *strong* for a
target language when every assignment to B restricts every relation to that
language (or to the empty relation).  We enumerate the 2**|B| assignments and
solve each residual instance natively.  The module never searches for B and
never claims that a small backdoor exists for arbitrary SAT instances.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import engine


@dataclass(frozen=True)
class Constraint:
    scope: tuple[int, ...]
    relation: frozenset[tuple[int, ...]]


def _validate(n: int, constraints: tuple[Constraint, ...], backdoor: tuple[int, ...]) -> None:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if len(set(backdoor)) != len(backdoor) or any(v < 0 or v >= n for v in backdoor):
        raise ValueError("backdoor must contain distinct in-range variables")
    for c in constraints:
        if len(set(c.scope)) != len(c.scope) or any(v < 0 or v >= n for v in c.scope):
            raise ValueError("constraint scope is invalid")
        if any(len(row) != len(c.scope) or any(bit not in (0, 1) for bit in row)
               for row in c.relation):
            raise ValueError("relation tuple has the wrong Boolean shape")


def restrict(c: Constraint, assignment: dict[int, int]) -> Constraint:
    """Restrict assigned scope coordinates and preserve the remaining order."""
    keep = tuple(v for v in c.scope if v not in assignment)
    positions = {v: i for i, v in enumerate(c.scope)}
    rows = frozenset(tuple(row[positions[v]] for v in keep)
                     for row in c.relation
                     if all(row[positions[v]] == bit for v, bit in assignment.items()
                            if v in positions))
    return Constraint(keep, rows)


def _is_empty(c: Constraint) -> bool:
    return not c.relation


def _horn_clauses(c: Constraint) -> list[tuple[frozenset[int], int | None]]:
    """Return all valid canonical Horn clauses for an AND-closed relation.

    A clause is represented as (antecedent, consequent).  ``None`` means a
    purely negative clause.  The enumeration is polynomial in the explicit
    truth-table length (although intentionally not optimized).
    """
    m = len(c.scope)
    rows = c.relation
    clauses: list[tuple[frozenset[int], int | None]] = []
    for mask in range(1 << m):
        antecedent = frozenset(i for i in range(m) if mask >> i & 1)
        if all(not all(row[i] for i in antecedent) for row in rows):
            clauses.append((antecedent, None))
        for consequent in range(m):
            if consequent in antecedent:
                continue
            if all(not all(row[i] for i in antecedent) or row[consequent]
                   for row in rows):
                clauses.append((antecedent, consequent))
    return clauses


def solve_horn(n: int, constraints: tuple[Constraint, ...]) -> tuple[bool, tuple[int, ...] | None]:
    """Solve a conjunction of explicit AND-closed relations by forward chaining."""
    clauses: list[tuple[frozenset[int], int | None]] = []
    for c in constraints:
        if _is_empty(c):
            return False, None
        local = _horn_clauses(c)
        for antecedent, consequent in local:
            mapped = frozenset(c.scope[i] for i in antecedent)
            mapped_consequent = None if consequent is None else c.scope[consequent]
            clauses.append((mapped, mapped_consequent))

    value = [0] * n
    changed = True
    while changed:
        changed = False
        for antecedent, consequent in clauses:
            if not all(value[v] for v in antecedent):
                continue
            if consequent is None:
                return False, None
            if value[consequent] == 0:
                value[consequent] = 1
                changed = True
    return True, tuple(value)


def _dot(mask: int, row: tuple[int, ...]) -> int:
    return sum(row[i] for i in range(len(row)) if mask >> i & 1) & 1


def _affine_equations(c: Constraint) -> list[tuple[int, int]]:
    """Return a complete (possibly redundant) GF(2) equation list."""
    if not c.relation:
        raise ValueError("empty relation has no affine base")
    rows = sorted(c.relation)
    base = rows[0]
    differences = [tuple(x ^ y for x, y in zip(row, base)) for row in rows[1:]]
    equations = []
    for mask in range(1, 1 << len(c.scope)):
        if all(_dot(mask, d) == 0 for d in differences):
            equations.append((mask, _dot(mask, base)))
    return equations


def _solve_linear(n: int, equations: Iterable[tuple[int, int]]) -> tuple[bool, tuple[int, ...] | None]:
    """Solve x-mask = rhs equations over GF(2), returning one witness."""
    rows = [[mask, rhs & 1] for mask, rhs in equations if mask]
    pivot_row = 0
    pivot_for_column: dict[int, int] = {}
    for column in range(n):
        pivot = next((i for i in range(pivot_row, len(rows))
                      if (rows[i][0] >> column) & 1), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        for i in range(len(rows)):
            if i != pivot_row and ((rows[i][0] >> column) & 1):
                rows[i][0] ^= rows[pivot_row][0]
                rows[i][1] ^= rows[pivot_row][1]
        pivot_for_column[column] = pivot_row
        pivot_row += 1
    for mask, rhs in rows:
        if mask == 0 and rhs:
            return False, None
    value = [0] * n
    for column, row in pivot_for_column.items():
        mask, rhs = rows[row]
        rest = mask & ~(1 << column)
        value[column] = rhs ^ (sum(value[i] for i in range(n) if rest >> i & 1) & 1)
    return True, tuple(value)


def solve_affine(n: int, constraints: tuple[Constraint, ...]) -> tuple[bool, tuple[int, ...] | None]:
    """Solve a conjunction of explicit affine relations by Gaussian elimination."""
    equations: list[tuple[int, int]] = []
    for c in constraints:
        if _is_empty(c):
            return False, None
        local = _affine_equations(c)
        for mask, rhs in local:
            mapped = 0
            for i, variable in enumerate(c.scope):
                if mask >> i & 1:
                    mapped |= 1 << variable
            equations.append((mapped, rhs))
    return _solve_linear(n, equations)


def _target_tag(target: str) -> str:
    if target == "HORN":
        return "AND"
    if target == "AFFINE":
        return "MIN"
    raise ValueError("target must be HORN or AFFINE")


def _branch_constraints(constraints: tuple[Constraint, ...], assignment: dict[int, int]) -> tuple[Constraint, ...]:
    return tuple(restrict(c, assignment) for c in constraints)


def _check_witness(n: int, constraints: tuple[Constraint, ...], witness: tuple[int, ...]) -> bool:
    if len(witness) != n or any(bit not in (0, 1) for bit in witness):
        return False
    for c in constraints:
        row = tuple(witness[v] for v in c.scope)
        if row not in c.relation:
            return False
    return True


def solve_with_backdoor(n: int, constraints: tuple[Constraint, ...], backdoor: tuple[int, ...],
                        target: str) -> dict[str, object]:
    """Solve or conservatively return UNKNOWN for a supplied strong backdoor."""
    constraints = tuple(constraints)
    backdoor = tuple(backdoor)
    _validate(n, constraints, backdoor)
    tag = _target_tag(target)
    budget = 1 << len(backdoor)
    branches: list[dict[str, object]] = []
    for bits in product((0, 1), repeat=len(backdoor)):
        assignment = dict(zip(backdoor, bits))
        residual = _branch_constraints(constraints, assignment)
        bad = []
        for index, c in enumerate(residual):
            signature = sorted(engine.relation_signature(c.relation, len(c.scope)))
            if c.relation and tag not in signature:
                bad.append({"constraint": index, "scope": list(c.scope),
                            "signature": signature})
        branch = {"assignment": list(bits), "residual_signatures": [
            sorted(engine.relation_signature(c.relation, len(c.scope))) for c in residual]}
        if bad:
            branch["status"] = "NOT_TARGET"
            branch["counterexample"] = bad[0]
            branches.append(branch)
            return {"status": "UNKNOWN", "reason": "NOT_STRONG_BACKDOOR",
                    "target": target, "backdoor": list(backdoor), "parameter_k": len(backdoor),
                    "branch_budget": budget, "branches": branches}
        if target == "HORN":
            sat, witness = solve_horn(n, residual)
        else:
            sat, witness = solve_affine(n, residual)
        branch["status"] = "SAT" if sat else "UNSAT"
        if sat:
            full = list(witness or ())
            for variable, bit in assignment.items():
                full[variable] = bit
            witness_tuple = tuple(full)
            if not _check_witness(n, constraints, witness_tuple):
                raise AssertionError("native branch produced an invalid original witness")
            branch["witness"] = list(witness_tuple)
            branches.append(branch)
            return {"status": "SAT", "target": target, "backdoor": list(backdoor),
                    "branches": branches, "witness": list(witness_tuple),
                    "parameter_k": len(backdoor), "branch_budget": budget,
                    "enumerated_assignments": len(branches)}
        branches.append(branch)
    return {"status": "UNSAT", "target": target, "backdoor": list(backdoor),
            "branches": branches, "parameter_k": len(backdoor),
            "branch_budget": budget, "enumerated_assignments": len(branches)}
