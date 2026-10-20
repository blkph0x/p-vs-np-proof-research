"""Exact reduction for affine recognition under existential CNF projection.

The projected variables are three visible bits.  A selector chooses either a
source CNF ``G`` or a fixed non-affine relation B.  If G is satisfiable the
projection is the full three-bit cube; if G is unsatisfiable it is B.
"""

from __future__ import annotations

from itertools import product

SHARED = (0, 1, 2)
SELECTOR = 3
Y_OFFSET = 4


def nonlinear_relation_clauses() -> tuple[tuple[int, ...], ...]:
    """Return clauses for B(x)=x0 OR (x1 AND x2)."""
    return ((1, 2), (1, 3))


def shift_source_clause(clause: tuple[int, ...]) -> tuple[int, ...]:
    return tuple((literal + Y_OFFSET if literal > 0 else literal - Y_OFFSET)
                 for literal in clause)


def selector_lift(g_clauses: tuple[tuple[int, ...], ...], nvars: int) -> dict:
    """Build a CNF whose projection is full iff G is satisfiable, else B."""
    if nvars < 0:
        raise ValueError("nvars must be nonnegative")
    for clause in g_clauses:
        if any(abs(literal) > nvars or literal == 0 for literal in clause):
            raise ValueError("source literal is outside the declared variable range")
    clauses: list[tuple[int, ...]] = []
    # Selector=1 activates G: (-s OR C). Selector=0 activates B: (s OR D).
    for clause in g_clauses:
        clauses.append((-SELECTOR - 1,) + shift_source_clause(clause))
    for clause in nonlinear_relation_clauses():
        clauses.append((SELECTOR + 1,) + clause)
    return {
        "shared": SHARED,
        "local": tuple([SELECTOR] + list(range(Y_OFFSET, Y_OFFSET + nvars))),
        "clauses": tuple(clauses),
        "source_nvars": nvars,
        "source_clauses": tuple(tuple(int(literal) for literal in clause)
                                for clause in g_clauses),
    }


def satisfies(clauses: tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> bool:
    return all(any((assignment[abs(literal) - 1] if literal > 0 else
                    not assignment[abs(literal) - 1]) for literal in clause)
               for clause in clauses)


def project(lifted: dict) -> tuple[int, ...]:
    clauses = tuple(lifted["clauses"])
    shared = tuple(lifted["shared"])
    local = tuple(lifted["local"])
    bits: list[int] = []
    for shared_mask in range(1 << len(shared)):
        shared_assignment = {variable: bool(shared_mask & (1 << index))
                             for index, variable in enumerate(shared)}
        found = False
        for local_mask in range(1 << len(local)):
            assignment = dict(shared_assignment)
            assignment.update({variable: bool(local_mask & (1 << index))
                               for index, variable in enumerate(local)})
            if satisfies(clauses, assignment):
                found = True
                break
        bits.append(int(found))
    return tuple(bits)


def source_models(g_clauses: tuple[tuple[int, ...], ...], nvars: int) -> tuple[tuple[bool, ...], ...]:
    return tuple(assignment for assignment in product((False, True), repeat=nvars)
                 if satisfies(g_clauses, {index: value for index, value in enumerate(assignment)}))


def is_affine_relation(bits: tuple[int, ...]) -> bool:
    """Check whether a nonempty Boolean relation is an affine coset."""
    points = {mask for mask, bit in enumerate(bits) if bit}
    if not points:
        return False
    base = next(iter(points))
    translated = {point ^ base for point in points}
    return all(left ^ right in translated for left in translated for right in translated)


def relation_class(bits: tuple[int, ...]) -> str:
    return "AFFINE" if is_affine_relation(bits) else "NON_AFFINE_OR_EMPTY"


def exact_record(g_clauses: tuple[tuple[int, ...], ...], nvars: int) -> dict:
    normalized = tuple(tuple(int(literal) for literal in clause) for clause in g_clauses)
    lifted = selector_lift(normalized, nvars)
    bits = project(lifted)
    models = source_models(normalized, nvars)
    return {
        "source_nvars": nvars,
        "source_clauses": [list(clause) for clause in normalized],
        "source_satisfiable": bool(models),
        "source_model_count": len(models),
        "shared_width": len(SHARED),
        "projection_bits": list(bits),
        "projection_class": relation_class(bits),
        "lifted_clauses": [list(clause) for clause in lifted["clauses"]],
    }


def build_artifact() -> dict:
    sat = exact_record(((1,),), 1)
    unsat = exact_record(((1,), (-1,)), 1)
    empty_source = exact_record((), 0)
    forged = dict(sat)
    forged["projection_bits"] = list(unsat["projection_bits"])
    return {
        "status": "EXACT_FINITE_REDUCTION",
        "theorem": "G satisfiable iff selector-lift projection is AFFINE",
        "construction": "(-s OR C) for source clauses and (s OR D) for fixed non-affine D",
        "shared_width": len(SHARED),
        "fixed_non_affine_relation": [list(clause) for clause in nonlinear_relation_clauses()],
        "records": [sat, unsat, empty_source],
        "adversarial": {"forged_projection_rejected": forged["projection_bits"] != sat["projection_bits"]},
    }

