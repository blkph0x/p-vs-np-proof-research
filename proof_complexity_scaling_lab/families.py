"""Adversarial CNF families used by the proof-complexity scaling audit."""
from __future__ import annotations

from itertools import combinations, product


def all_assignment_clauses(nvars: int) -> tuple[tuple[int, ...], ...]:
    """One clause for every complete assignment, falsified by that assignment."""
    return tuple(
        tuple((variable + 1) if not bit else -(variable + 1)
              for variable, bit in enumerate(bits))
        for bits in product((0, 1), repeat=nvars)
    )


def pigeonhole(pigeons: int, holes: int) -> tuple[int, tuple[tuple[int, ...], ...]]:
    """CNF asserting that ``pigeons`` inject into ``holes``."""
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [
        tuple(variable(pigeon, hole) for hole in range(holes))
        for pigeon in range(pigeons)
    ]
    clauses += [
        (-variable(pigeon, left), -variable(pigeon, right))
        for pigeon in range(pigeons)
        for left, right in combinations(range(holes), 2)
    ]
    clauses += [
        (-variable(left, hole), -variable(right, hole))
        for hole in range(holes)
        for left, right in combinations(range(pigeons), 2)
    ]
    return pigeons * holes, tuple(clauses)


def controls() -> tuple[dict, ...]:
    """Return the fixed scaling campaign.

    The all-assignment family is kept through ten variables.  Its input has
    ``n * 2**n`` literal occurrences, so its observed exponential-in-``n``
    trace is not an exponential-in-input-length claim.  The pigeonhole
    family uses ``h + 1`` pigeons and ``h`` holes for ``h = 1..8``; its input
    size is polynomial in ``h`` and the formulas have a direct counting proof
    of unsatisfiability.
    """
    rows = []
    for nvars in range(1, 11):
        clauses = all_assignment_clauses(nvars)
        rows.append({
            "name": f"all_assignments_n{nvars}",
            "family": "all_assignments",
            "parameter": nvars,
            "nvars": nvars,
            "clauses": clauses,
        })
    for holes in range(1, 9):
        nvars, clauses = pigeonhole(holes + 1, holes)
        rows.append({
            "name": f"pigeonhole_{holes + 1}_{holes}",
            "family": "pigeonhole",
            "parameter": holes,
            "pigeons": holes + 1,
            "holes": holes,
            "nvars": nvars,
            "clauses": clauses,
        })
    return tuple(rows)
