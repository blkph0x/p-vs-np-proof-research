"""Complete bounded-width weakening-resolution closure for small CNFs."""
from __future__ import annotations

from collections import deque
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def normalize_clause(clause):
    values = {int(lit) for lit in clause}
    if 0 in values:
        raise ValueError("literal zero is not allowed")
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, pivot):
    positive = pivot + 1
    left_set, right_set = set(left), set(right)
    if positive in left_set and -positive in right_set:
        result = (left_set - {positive}) | (right_set - {-positive})
    elif -positive in left_set and positive in right_set:
        result = (left_set - {-positive}) | (right_set - {positive})
    else:
        raise ValueError(("pivot absent with opposite polarity", pivot, left, right))
    return normalize_clause(result)


def weakenings(clause, nvars, width):
    """Enumerate every non-tautological weakening of a clause up to ``width``."""
    present = {abs(lit) for lit in clause}
    missing = [variable for variable in range(1, nvars + 1) if variable not in present]
    for size in range(width - len(clause) + 1):
        for chosen in combinations(missing, size):
            for signs in product((False, True), repeat=size):
                yield normalize_clause(tuple(clause) + tuple(
                    variable if positive else -variable
                    for variable, positive in zip(chosen, signs)))


class BoundedResolution:
    """Saturate all width-``w`` weakening/resolution consequences."""

    def __init__(self, nvars, clauses, width, *, max_clauses=10000,
                 max_steps=100000):
        if type(nvars) is not int or nvars < 0:
            raise ValueError("nvars must be a nonnegative integer")
        if type(width) is not int or width < 0:
            raise ValueError("width must be a nonnegative integer")
        self.nvars, self.width = nvars, width
        self.max_clauses, self.max_steps = max_clauses, max_steps
        if max_clauses < 1 or max_steps < 1:
            raise ValueError("resource caps must be positive")
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

    def solve(self):
        known = set()
        records = []
        queue = deque()
        stats = {"initial_clauses": len(self.initial), "known_clauses": 0,
                 "processed_clauses": 0, "candidate_steps": 0,
                 "weakening_steps": 0, "resolution_steps": 0}

        def add(clause, record):
            if clause in known:
                return False
            if len(known) >= self.max_clauses:
                return None
            known.add(clause)
            records.append(record)
            queue.append(clause)
            stats["known_clauses"] = len(known)
            return True

        for clause in self.initial:
            outcome = add(clause, {"kind": "axiom", "clause": clause})
            if outcome is None:
                return self._unknown("CLAUSE_CAP", known, records, stats)
        if () in known:
            return self._unsat(known, records, stats)

        while queue:
            current = queue.popleft()
            stats["processed_clauses"] += 1
            for weakened in weakenings(current, self.nvars, self.width):
                if weakened == current:
                    continue
                stats["candidate_steps"] += 1
                stats["weakening_steps"] += 1
                if stats["candidate_steps"] > self.max_steps:
                    return self._unknown("STEP_CAP", known, records, stats)
                outcome = add(weakened, {"kind": "weaken", "parent": current,
                                         "clause": weakened})
                if outcome is None:
                    return self._unknown("CLAUSE_CAP", known, records, stats)
            existing = tuple(sorted(known))
            for other in existing:
                for pivot in range(self.nvars):
                    if ((pivot + 1 in current and -(pivot + 1) in other) or
                            (-(pivot + 1) in current and pivot + 1 in other)):
                        result = resolve(current, other, pivot)
                        if result is None or len(result) > self.width:
                            continue
                        stats["candidate_steps"] += 1
                        stats["resolution_steps"] += 1
                        if stats["candidate_steps"] > self.max_steps:
                            return self._unknown("STEP_CAP", known, records, stats)
                        outcome = add(result, {"kind": "resolve", "left": current,
                                               "right": other, "pivot": pivot,
                                               "clause": result})
                        if outcome is None:
                            return self._unknown("CLAUSE_CAP", known, records, stats)
                        if result == ():
                            return self._unsat(known, records, stats)
        return {"status": "UNKNOWN", "reason": "NO_WIDTH_W_REFUTATION",
                "clauses": [list(clause) for clause in sorted(known)],
                "proof": records, "stats": stats}

    @staticmethod
    def _unsat(known, records, stats):
        return {"status": "UNSAT", "clauses": [list(clause) for clause in sorted(known)],
                "proof": records, "stats": stats}

    @staticmethod
    def _unknown(reason, known, records, stats):
        return {"status": "UNKNOWN", "reason": reason,
                "clauses": [list(clause) for clause in sorted(known)],
                "proof": records, "stats": stats}


def source_hashes():
    names = ("resolution.py", "run_audit.py", "THEOREM.md", "review.py",
             "test_resolution.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}
