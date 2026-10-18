"""Exact controls for random affine isolation of Boolean solution sets."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class IsolationResult:
    rows: tuple[int, ...]
    target: int
    survivors: tuple[int, ...]


def all_matrices(n: int, r: int):
    if type(n) is not int or type(r) is not int or n < 0 or r < 0:
        raise ValueError("dimensions must be nonnegative integers")
    total = 1 << n
    if r == 0:
        yield ()
        return
    # A row is an n-bit linear form.  Product order is deterministic.
    def visit(prefix):
        if len(prefix) == r:
            yield tuple(prefix)
            return
        for row in range(total):
            yield from visit(prefix + [row])
    yield from visit([])


def all_targets(r: int):
    if type(r) is not int or r < 0:
        raise ValueError("target dimension must be a nonnegative integer")
    return range(1 << r)


def hash_value(rows, assignment: int) -> int:
    if type(assignment) is not int or assignment < 0:
        raise ValueError("assignment must be a nonnegative bit mask")
    value = 0
    for index, row in enumerate(rows):
        value |= ((row & assignment).bit_count() & 1) << index
    return value


def survivors(assignments, rows, target: int) -> tuple[int, ...]:
    assignments = tuple(assignments)
    if type(target) is not int or target < 0 or target >= (1 << len(rows)):
        raise ValueError("target is outside the hash range")
    return tuple(x for x in assignments if hash_value(rows, x) == target)


def choose_rank(solution_count: int) -> int:
    """Rank r with 1/4 <= s/2^r <= 1/2 for s>0."""
    if type(solution_count) is not int or solution_count <= 0:
        raise ValueError("solution count must be positive")
    return math.ceil(math.log2(solution_count)) + 1


def exact_isolation_probability(assignments, n: int, r: int) -> tuple[int, int]:
    """Return (isolating hash pairs, all hash pairs) by exhaustive replay."""
    assignments = tuple(assignments)
    successes = total = 0
    for rows in all_matrices(n, r):
        for target in all_targets(r):
            total += 1
            if len(survivors(assignments, rows, target)) == 1:
                successes += 1
    return successes, total


def second_moment_bound(solution_count: int, r: int) -> tuple[float, float]:
    """Return mu and the proven lower bound mu-mu^2."""
    if type(solution_count) is not int or solution_count <= 0:
        raise ValueError("solution count must be positive")
    if type(r) is not int or r < 0:
        raise ValueError("rank must be a nonnegative integer")
    mu = solution_count / (1 << r)
    return mu, mu - mu * mu


def random_hash(n: int, r: int, rng: random.Random) -> tuple[int, ...]:
    if type(n) is not int or type(r) is not int or n < 0 or r < 0:
        raise ValueError("dimensions must be nonnegative integers")
    return tuple(rng.randrange(1 << n) for _ in range(r))


def models(n: int, clauses) -> tuple[int, ...]:
    """Evaluate a CNF using signed integer literals and return model masks."""
    if type(n) is not int or n < 0 or type(clauses) is not list:
        raise ValueError("malformed CNF")
    for clause in clauses:
        if type(clause) is not list:
            raise ValueError("malformed clause")
        for literal in clause:
            if type(literal) is not int or literal == 0 or abs(literal) > n:
                raise ValueError("literal outside declared variable range")
    out = []
    for assignment in range(1 << n):
        if all(any(((assignment >> (abs(literal) - 1)) & 1) == (literal > 0)
                   for literal in clause) for clause in clauses):
            out.append(assignment)
    return tuple(out)


def isolate_cnf(n: int, clauses, rows, target: int) -> IsolationResult:
    assignment_set = models(n, clauses)
    return IsolationResult(tuple(rows), target, survivors(assignment_set, rows, target))

