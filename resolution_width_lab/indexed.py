"""Indexed bounded-width resolution closure.

This is an optimization of the reference closure, not a new inference rule.
Clauses are indexed by their literals so a current clause is resolved only
against clauses that contain the opposite pivot literal.  The reference
implementation scans every known clause; keeping both implementations lets
the tests distinguish a work reduction from a change in proof semantics.
"""
from __future__ import annotations

from collections import defaultdict, deque

from resolution import normalize_clause, resolve, weakenings


class IndexedBoundedResolution:
    """Saturate all width-``w`` weakening/resolution consequences."""

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
        self.original = []
        self.initial = []
        for raw in clauses:
            canonical = normalize_clause(raw)
            if canonical is None:
                continue
            if any(abs(lit) > nvars for lit in canonical):
                raise ValueError("literal outside declared variable range")
            self.original.append(canonical)
            if len(canonical) <= width:
                self.initial.append(canonical)

    def solve(self, seed_clauses=()):
        known = set()
        queue = deque()
        by_literal = defaultdict(set)
        stats = {"initial_clauses": len(self.initial), "known_clauses": 0,
                 "processed_clauses": 0, "candidate_steps": 0,
                 "weakening_steps": 0, "resolution_steps": 0,
                 "indexed_resolution_pairs": 0}

        def add(clause, record):
            if clause in known:
                return False
            if len(known) >= self.max_clauses:
                return None
            known.add(clause)
            queue.append(clause)
            for literal in clause:
                by_literal[literal].add(clause)
            stats["known_clauses"] = len(known)
            return True

        for raw in seed_clauses:
            clause = normalize_clause(raw)
            if clause is None or len(clause) > self.width:
                continue
            outcome = add(clause, {"kind": "seed", "clause": clause})
            if outcome is None:
                return self._unknown("CLAUSE_CAP", known, stats)
        for clause in self.initial:
            outcome = add(clause, {"kind": "axiom", "clause": clause})
            if outcome is None:
                return self._unknown("CLAUSE_CAP", known, stats)
        if () in known:
            return self._unsat(known, stats)

        while queue:
            current = queue.popleft()
            stats["processed_clauses"] += 1
            for weakened in weakenings(current, self.nvars, self.width):
                if weakened == current:
                    continue
                stats["candidate_steps"] += 1
                stats["weakening_steps"] += 1
                if stats["candidate_steps"] > self.max_steps:
                    return self._unknown("STEP_CAP", known, stats)
                outcome = add(weakened, {"kind": "weaken", "parent": current,
                                         "clause": weakened})
                if outcome is None:
                    return self._unknown("CLAUSE_CAP", known, stats)

            # Each opposite-literal pair is considered when the first member
            # reaches the queue.  This covers every resolvable pair because
            # both clauses are eventually indexed, while avoiding unrelated
            # clause scans from the reference implementation.
            for literal in current:
                for other in tuple(by_literal[-literal]):
                    stats["indexed_resolution_pairs"] += 1
                    pivot = abs(literal) - 1
                    result = resolve(current, other, pivot)
                    if result is None or len(result) > self.width:
                        continue
                    stats["candidate_steps"] += 1
                    stats["resolution_steps"] += 1
                    if stats["candidate_steps"] > self.max_steps:
                        return self._unknown("STEP_CAP", known, stats)
                    outcome = add(result, {"kind": "resolve", "left": current,
                                           "right": other, "pivot": pivot,
                                           "clause": result})
                    if outcome is None:
                        return self._unknown("CLAUSE_CAP", known, stats)
                    if result == ():
                        return self._unsat(known, stats)
        return self._unknown("NO_WIDTH_W_REFUTATION", known, stats)

    @staticmethod
    def _unsat(known, stats):
        return {"status": "UNSAT", "reason": None,
                "clauses": [list(clause) for clause in sorted(known)],
                "proof": [], "stats": stats}

    @staticmethod
    def _unknown(reason, known, stats):
        return {"status": "UNKNOWN", "reason": reason,
                "clauses": [list(clause) for clause in sorted(known)],
                "proof": [], "stats": stats}
