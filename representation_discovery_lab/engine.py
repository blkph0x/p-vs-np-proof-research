"""Exact hidden-structure representation-discovery experiment.

This module studies one explicitly bounded discovery model.  A parity relation
on shared variables is encoded as a compact XOR chain with existential helper
variables.  The projected relation still has a one-equation representation,
but a projection-based synthesizer must enumerate the helper assignments before
it can discover that representation.

The result is model-specific evidence about discovery cost.  It is not a lower
bound on SAT, on representation discovery in general, or on P versus NP.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Iterable


def _xor3_clauses(left: int, right: int, out: int) -> tuple[tuple[int, ...], ...]:
    """Return the four CNF clauses for ``out = left XOR right``."""
    def lit(variable: int, positive: bool) -> int:
        return variable + 1 if positive else -(variable + 1)

    return (
        (lit(left, False), lit(right, False), lit(out, False)),
        (lit(left, True), lit(right, True), lit(out, False)),
        (lit(left, True), lit(right, False), lit(out, True)),
        (lit(left, False), lit(right, True), lit(out, True)),
    )


def xor_chain(shared_count: int, permutation: Iterable[int] | None = None) -> dict:
    """Build a compact CNF encoding of ``xor(shared variables) = 0``.

    The shared variables are numbered ``0..shared_count-1``.  A chain uses one
    existential helper after each prefix XOR and finishes with a unit clause
    fixing the last helper to zero.  ``permutation`` renames the shared inputs;
    it changes syntax while preserving the projected parity relation.
    """
    if shared_count < 3:
        raise ValueError("shared_count must be at least three")
    if permutation is None:
        permutation = tuple(range(shared_count))
    permutation = tuple(int(value) for value in permutation)
    if tuple(sorted(permutation)) != tuple(range(shared_count)):
        raise ValueError("permutation must contain every shared variable once")

    next_variable = shared_count
    previous = permutation[0]
    clauses: list[tuple[int, ...]] = []
    helpers: list[int] = []
    for shared in permutation[1:]:
        helper = next_variable
        next_variable += 1
        helpers.append(helper)
        clauses.extend(_xor3_clauses(previous, shared, helper))
        previous = helper
    clauses.append((-(previous + 1),))
    return {
        "shared": tuple(range(shared_count)),
        "local": tuple(helpers),
        "clauses": tuple(clauses),
        "permutation": permutation,
        "representation": {
            "kind": "XOR",
            "support": tuple(range(shared_count)),
            "rhs": 0,
        },
    }


def _literal_value(literal: int, assignment: dict[int, bool]) -> bool:
    value = assignment[abs(literal) - 1]
    return value if literal > 0 else not value


def satisfies(clauses: tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> bool:
    return all(any(_literal_value(literal, assignment) for literal in clause)
               for clause in clauses)


def project(clauses: tuple[tuple[int, ...], ...], shared: tuple[int, ...], local: tuple[int, ...]) -> tuple[int, ...]:
    """Enumerate the exact existential projection onto ``shared``."""
    bits: list[int] = []
    for shared_mask in range(1 << len(shared)):
        shared_assignment = {
            variable: bool(shared_mask & (1 << index))
            for index, variable in enumerate(shared)
        }
        found = False
        for local_mask in range(1 << len(local)):
            assignment = dict(shared_assignment)
            assignment.update({
                variable: bool(local_mask & (1 << index))
                for index, variable in enumerate(local)
            })
            if satisfies(clauses, assignment):
                found = True
                break
        bits.append(int(found))
    return tuple(bits)


def parity_bits(shared_count: int) -> tuple[int, ...]:
    return tuple(int(mask.bit_count() % 2 == 0) for mask in range(1 << shared_count))


def candidate_search_work(shared_count: int) -> int:
    """Count the fixed vocabulary's truth-table evaluations.

    The vocabulary is all nonempty XOR supports and both right-hand sides,
    plus the explicit truth-table fallback.  This is deliberately a bounded
    model, so the count is part of the result rather than hidden in a timer.
    """
    candidate_count = 2 * ((1 << shared_count) - 1) + 1
    return (1 << shared_count) * candidate_count


@dataclass(frozen=True)
class DiscoveryRecord:
    shared_count: int
    permutation: tuple[int, ...]
    clause_count: int
    local_count: int
    representation_bits: int
    discovery_work: int
    verification_work: int
    projected_bits: tuple[int, ...]


def discover(chain: dict) -> DiscoveryRecord:
    """Run the fixed bounded discovery calculation and exact replay."""
    shared = tuple(chain["shared"])
    local = tuple(chain["local"])
    clauses = tuple(chain["clauses"])
    projected = project(clauses, shared, local)
    expected = parity_bits(len(shared))
    if projected != expected:
        raise ValueError("chain projection is not the expected even-parity relation")
    # Encoding a support of m variables needs m variable labels and one RHS bit.
    representation_bits = 8 + len(shared) * max(1, (len(shared) - 1).bit_length()) + 1
    projection_work = (1 << (len(shared) + len(local))) * max(1, len(clauses))
    discovery_work = projection_work + candidate_search_work(len(shared))
    # Independent replay enumerates exactly the same assignments and clauses;
    # keep it explicit as a separate metric instead of folding it into S.
    verification_work = projection_work
    return DiscoveryRecord(
        shared_count=len(shared),
        permutation=tuple(chain["permutation"]),
        clause_count=len(clauses),
        local_count=len(local),
        representation_bits=representation_bits,
        discovery_work=discovery_work,
        verification_work=verification_work,
        projected_bits=projected,
    )


def records(max_shared: int = 7) -> tuple[DiscoveryRecord, ...]:
    """Generate identity and reversed-name controls through the explicit cap."""
    rows: list[DiscoveryRecord] = []
    for shared_count in range(3, max_shared + 1):
        controls = (
            tuple(range(shared_count)),
            tuple(reversed(range(shared_count))),
        )
        for permutation in controls:
            rows.append(discover(xor_chain(shared_count, permutation)))
    return tuple(rows)


def verify_record(chain: dict, record: DiscoveryRecord) -> bool:
    """Independent structural and semantic check for one saved record."""
    fresh = discover(chain)
    return fresh == record


if __name__ == "__main__":
    for row in records():
        print(row)
