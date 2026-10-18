"""Bit-mask bounded-width resolution closure.

The tuple implementation remains the reference.  This module stores each
clause as ``(positive_mask, negative_mask)`` and keeps the same weakening and
resolution rules, so it can test whether representation cost is the current
frontier on the PHP(5,4) stress row.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations, product


def encode(clause, nvars):
    positive = negative = 0
    for literal in clause:
        if literal == 0 or abs(literal) > nvars:
            raise ValueError("literal outside declared variable range")
        bit = 1 << (abs(literal) - 1)
        if literal > 0:
            positive |= bit
        else:
            negative |= bit
    if positive & negative:
        return None
    return positive, negative


def decode(key):
    positive, negative = key
    literals = [variable + 1 for variable in range(positive.bit_length())
                if positive & (1 << variable)]
    literals += [-(variable + 1) for variable in range(negative.bit_length())
                 if negative & (1 << variable)]
    return tuple(sorted(literals, key=lambda literal: (abs(literal), literal < 0)))


def clause_width(key):
    return (key[0] | key[1]).bit_count()


def weakenings(key, nvars, bound):
    positive, negative = key
    present = positive | negative
    missing = [variable for variable in range(nvars) if not present & (1 << variable)]
    for size in range(bound - clause_width(key) + 1):
        for chosen in combinations(missing, size):
            for signs in product((False, True), repeat=size):
                next_positive, next_negative = positive, negative
                for variable, is_positive in zip(chosen, signs):
                    if is_positive:
                        next_positive |= 1 << variable
                    else:
                        next_negative |= 1 << variable
                yield next_positive, next_negative


def resolve(left, right, pivot):
    bit = 1 << pivot
    left_positive, left_negative = left
    right_positive, right_negative = right
    if left_positive & bit and right_negative & bit:
        positive = (left_positive ^ bit) | right_positive
        negative = left_negative | (right_negative ^ bit)
    elif left_negative & bit and right_positive & bit:
        positive = left_positive | (right_positive ^ bit)
        negative = (left_negative ^ bit) | right_negative
    else:
        raise AssertionError((left, right, pivot))
    if positive & negative:
        return None
    return positive, negative


class BitsetBoundedResolution:
    """Saturate the same finite bounded-width closure as the tuple solver."""

    def __init__(self, nvars, clauses, width, *, max_clauses=10000,
                 max_steps=100000):
        if type(nvars) is not int or nvars < 0:
            raise ValueError("nvars must be a nonnegative integer")
        if type(width) is not int or width < 0:
            raise ValueError("width must be a nonnegative integer")
        if max_clauses < 1 or max_steps < 1:
            raise ValueError("resource caps must be positive")
        self.nvars, self.width = nvars, width
        self.max_clauses, self.max_steps = max_clauses, max_steps
        self.initial = []
        for raw in clauses:
            clause = encode(raw, nvars)
            if clause is not None and clause_width(clause) <= self.width:
                self.initial.append(clause)

    def solve(self, seed_clauses=()):
        known = set()
        queue = []
        by_positive = defaultdict(set)
        by_negative = defaultdict(set)
        stats = {"initial_clauses": len(self.initial), "known_clauses": 0,
                 "processed_clauses": 0, "candidate_steps": 0,
                 "weakening_steps": 0, "resolution_steps": 0,
                 "indexed_resolution_pairs": 0}

        def add(clause):
            if clause in known:
                return False
            if len(known) >= self.max_clauses:
                return None
            known.add(clause)
            queue.append(clause)
            positive, negative = clause
            for pivot in range(self.nvars):
                bit = 1 << pivot
                if positive & bit:
                    by_positive[pivot].add(clause)
                if negative & bit:
                    by_negative[pivot].add(clause)
            stats["known_clauses"] = len(known)
            return True

        for raw in sorted(seed_clauses):
            clause = encode(raw, self.nvars)
            if clause is None or clause_width(clause) > self.width:
                continue
            outcome = add(clause)
            if outcome is None:
                return self._unknown("CLAUSE_CAP", known, stats)
        for clause in self.initial:
            outcome = add(clause)
            if outcome is None:
                return self._unknown("CLAUSE_CAP", known, stats)
        if (0, 0) in known:
            return self._unsat(known, stats)

        position = 0
        while position < len(queue):
            current = queue[position]
            position += 1
            stats["processed_clauses"] += 1
            for weakened in weakenings(current, self.nvars, self.width):
                if weakened == current:
                    continue
                stats["candidate_steps"] += 1
                stats["weakening_steps"] += 1
                if stats["candidate_steps"] > self.max_steps:
                    return self._unknown("STEP_CAP", known, stats)
                outcome = add(weakened)
                if outcome is None:
                    return self._unknown("CLAUSE_CAP", known, stats)
            positive, negative = current
            for pivot in range(self.nvars):
                bit = 1 << pivot
                candidates = by_negative[pivot] if positive & bit else ()
                if negative & bit:
                    candidates = tuple(candidates) + tuple(by_positive[pivot])
                for other in candidates:
                    stats["indexed_resolution_pairs"] += 1
                    result = resolve(current, other, pivot)
                    if result is None or clause_width(result) > self.width:
                        continue
                    stats["candidate_steps"] += 1
                    stats["resolution_steps"] += 1
                    if stats["candidate_steps"] > self.max_steps:
                        return self._unknown("STEP_CAP", known, stats)
                    outcome = add(result)
                    if outcome is None:
                        return self._unknown("CLAUSE_CAP", known, stats)
                    if result == (0, 0):
                        return self._unsat(known, stats)
        return self._unknown("NO_WIDTH_W_REFUTATION", known, stats)

    @staticmethod
    def _result(status, reason, known, stats):
        return {"status": status, "reason": reason,
                "clauses": [list(decode(clause)) for clause in sorted(known)],
                "proof": [], "stats": stats}

    @classmethod
    def _unsat(cls, known, stats):
        return cls._result("UNSAT", None, known, stats)

    @classmethod
    def _unknown(cls, reason, known, stats):
        return cls._result("UNKNOWN", reason, known, stats)
