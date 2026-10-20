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
    if type(shared_count) is not int or shared_count < 3:
        raise ValueError("shared_count must be at least three")
    if permutation is None:
        permutation = tuple(range(shared_count))
    permutation = tuple(permutation)
    if any(type(value) is not int for value in permutation):
        raise ValueError("permutation IDs must be exact integers")
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


def reorder_gadget_blocks(chain: dict, order: Iterable[int] | None = None,
                          duplicate_block: int | None = None) -> dict:
    """Return the same chain with its XOR-gadget blocks reordered or duplicated.

    The four clauses in each gadget are kept together.  Duplicating a block is
    a redundant syntactic control: it changes the input text but not the CNF
    relation.
    """
    block_count = len(chain["local"])
    if order is None:
        order = tuple(reversed(range(block_count)))
    order = tuple(order)
    if any(type(index) is not int for index in order):
        raise ValueError("order IDs must be exact integers")
    if sorted(order) != list(range(block_count)):
        raise ValueError("order must contain each gadget block once")
    blocks = [tuple(chain["clauses"][4 * index:4 * index + 4]) for index in range(block_count)]
    selected = [blocks[index] for index in order]
    if duplicate_block is not None:
        if type(duplicate_block) is not int or not 0 <= duplicate_block < block_count:
            raise ValueError("duplicate_block is out of range")
        selected.insert(1, blocks[duplicate_block])
    unit = tuple(chain["clauses"][4 * block_count:])
    return {**chain, "clauses": tuple(clause for block in selected for clause in block) + unit}


def rename_variables(chain: dict, mapping: dict[int, int]) -> dict:
    """Apply a bijective variable renaming to a chain, including metadata."""
    variables = set(chain["shared"]) | set(chain["local"])
    if any(type(value) is not int for pair in mapping.items() for value in pair):
        raise ValueError("renaming IDs must be exact integers")
    if set(mapping) != variables or set(mapping.values()) != variables:
        raise ValueError("mapping must be a permutation of all chain variables")
    clauses = tuple(tuple((1 if literal > 0 else -1) * (mapping[abs(literal) - 1] + 1)
                          for literal in clause) for clause in chain["clauses"])
    return {
        **chain,
        "shared": tuple(mapping[index] for index in chain["shared"]),
        "local": tuple(mapping[index] for index in chain["local"]),
        "clauses": clauses,
    }


def _literal_value(literal: int, assignment: dict[int, bool]) -> bool:
    value = assignment[abs(literal) - 1]
    return value if literal > 0 else not value


def satisfies(clauses: tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> bool:
    return all(any(_literal_value(literal, assignment) for literal in clause)
               for clause in clauses)


def project(clauses: tuple[tuple[int, ...], ...], shared: tuple[int, ...], local: tuple[int, ...]) -> tuple[int, ...]:
    """Enumerate the exact existential projection onto ``shared``."""
    if not all(isinstance(items, (tuple, list)) for items in (clauses, shared, local)):
        raise ValueError("clauses/shared/local must be lists or tuples")
    variable_ids = tuple(shared) + tuple(local)
    if (any(type(variable) is not int or variable < 0 for variable in variable_ids)
            or len(set(variable_ids)) != len(variable_ids)):
        raise ValueError("shared/local IDs must be exact, nonnegative, unique and disjoint")
    variables = set(variable_ids)
    for clause in clauses:
        if not isinstance(clause, (tuple, list)):
            raise ValueError("clauses must be lists or tuples")
        for literal in clause:
            if type(literal) is not int or literal == 0 or abs(literal)-1 not in variables:
                raise ValueError("nonzero exact literals must reference declared variables")
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
    encoded_representation_bits: int
    enumeration_discovery_work: int
    exhaustive_replay_work: int
    projected_bits: tuple[int, ...]


def discover(chain: dict) -> DiscoveryRecord:
    """Check the exact projection and calculate the declared schedule charges.

    Candidate enumeration is a symbolic charge, not an executed synthesis
    loop. Projection itself short-circuits; the full-schedule charge below is
    deliberately not an instrumentation count of those actual Python loops.
    """
    shared = tuple(chain["shared"])
    local = tuple(chain["local"])
    clauses = tuple(chain["clauses"])
    projected = project(clauses, shared, local)
    expected = parity_bits(len(shared))
    if projected != expected:
        raise ValueError("chain projection is not the expected even-parity relation")
    # Encoding a support of m variables needs m variable labels and one RHS bit.
    encoded_representation_bits = 8 + len(shared) * max(1, (len(shared) - 1).bit_length()) + 1
    projection_work = (1 << (len(shared) + len(local))) * max(1, len(clauses))
    enumeration_discovery_work = projection_work + candidate_search_work(len(shared))
    # This is the charge for a non-short-circuit replay schedule, not a count
    # of the actual short-circuit project() implementation above.
    exhaustive_replay_work = projection_work
    return DiscoveryRecord(
        shared_count=len(shared),
        permutation=tuple(chain["permutation"]),
        clause_count=len(clauses),
        local_count=len(local),
        encoded_representation_bits=encoded_representation_bits,
        enumeration_discovery_work=enumeration_discovery_work,
        exhaustive_replay_work=exhaustive_replay_work,
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
    """Recompute a producer record; independent replay is a separate module."""
    fresh = discover(chain)
    return fresh == record


if __name__ == "__main__":
    for row in records():
        print(row)
