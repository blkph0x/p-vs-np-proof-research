"""A structural GF(2) baseline for the hidden-XOR experiment.

This is deliberately separate from ``engine.py``.  It recognises the four
clauses of each XOR gadget, performs affine substitution over GF(2), and
never constructs the projected truth table.  The operation counter is a
transparent implementation charge, not a machine-independent lower bound.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineResult:
    status: str
    support: tuple[int, ...] = ()
    rhs: int = 0
    work: int = 0
    gadget_count: int = 0


def _normalise(clause: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(set(int(literal) for literal in clause), key=lambda value: (abs(value), value)))


def _satisfies(clause_set: set[tuple[int, ...]], assignment: dict[int, bool]) -> bool:
    return all(any((assignment[abs(literal) - 1] if literal > 0 else not assignment[abs(literal) - 1])
                   for literal in clause) for clause in clause_set)


def _is_xor_orientation(clauses: set[tuple[int, ...]], left: int, right: int, out: int) -> bool:
    """Check ``out = left XOR right`` on all eight assignments."""
    for mask in range(8):
        assignment = {variable: bool(mask & (1 << offset))
                      for offset, variable in enumerate((left, right, out))}
        expected = assignment[out] == (assignment[left] ^ assignment[right])
        if _satisfies(clauses, assignment) != expected:
            return False
    return True


def recover_xor_relation(clauses: tuple[tuple[int, ...], ...],
                         shared: tuple[int, ...]) -> BaselineResult:
    """Recover the affine relation forced on ``shared`` by XOR gadgets.

    Candidate triples are formed from the distinct three-variable clause
    supports.  Each orientation is checked by its constant-size truth table;
    the resulting equations are then solved by affine substitution, equivalent
    to Gaussian elimination for this acyclic chain family.
    """
    normalised = {_normalise(clause) for clause in clauses}
    work = len(clauses)
    groups: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    for clause in normalised:
        if len(clause) == 3:
            support = tuple(sorted({abs(literal) - 1 for literal in clause}))
            if len(support) == 3:
                groups.setdefault(support, set()).add(clause)
    equations: list[tuple[int, int, int]] = []
    for support, group in sorted(groups.items()):
        # A three-variable parity gadget is symmetric: every orientation is
        # equivalent to the equation a XOR b XOR c = 0.  Keep the support as
        # an unordered equation and choose the unknown variable during
        # elimination, rather than guessing which local helper is the output.
        work += 8
        if len(group) == 4 and _is_xor_orientation(group, support[0], support[1], support[2]):
            equations.append(support)
    units = [(-clause[0] - 1, 0) if clause[0] < 0 else (-clause[0] - 1, 1)
             for clause in normalised if len(clause) == 1]
    if len(units) != 1:
        return BaselineResult("UNKNOWN", work=work, gadget_count=len(equations))
    target, target_value = units[0]
    expressions: dict[int, tuple[int, int]] = {
        variable: (1 << index, 0) for index, variable in enumerate(shared)
    }
    remaining = list(equations)
    progress = True
    while remaining and progress:
        progress = False
        next_remaining: list[tuple[int, int, int]] = []
        for equation in remaining:
            known = [variable for variable in equation if variable in expressions]
            unknown = [variable for variable in equation if variable not in expressions]
            if len(known) == 2 and len(unknown) == 1:
                first_mask, first_rhs = expressions[known[0]]
                second_mask, second_rhs = expressions[known[1]]
                expressions[unknown[0]] = (first_mask ^ second_mask,
                                            first_rhs ^ second_rhs)
                work += 1
                progress = True
            else:
                next_remaining.append(equation)
        remaining = next_remaining
    if target not in expressions or remaining:
        return BaselineResult("UNKNOWN", work=work, gadget_count=len(equations))
    mask, offset = expressions[target]
    support = tuple(index for index, variable in enumerate(shared) if mask & (1 << index))
    # The unit target=target_value gives XOR(support) = target_value XOR offset.
    rhs = target_value ^ offset
    return BaselineResult("EXACT_AFFINE", support=support, rhs=rhs, work=work,
                          gadget_count=len(equations))


def expected_even_parity(shared: tuple[int, ...]) -> BaselineResult:
    return BaselineResult("EXACT_AFFINE", support=tuple(range(len(shared))), rhs=0)
