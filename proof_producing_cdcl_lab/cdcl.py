"""Small proof-producing CDCL solver for arbitrary CNF formulas.

The implementation is intentionally simple: full clause scans replace watched
literals, and first-UIP learning records every resolution step. Resource caps
return UNKNOWN, never a guessed SAT/UNSAT result.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent


def normalize_clause(clause):
    """Return a canonical clause, None for tautologies, and reject literal 0."""
    values = {int(lit) for lit in clause}
    if 0 in values:
        raise ValueError("literal zero is not allowed")
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def lit_var(lit: int) -> int:
    return abs(lit) - 1


def lit_value(lit: int) -> bool:
    return lit > 0


def clause_state(clause, assignment):
    """Return (satisfied, unassigned literals) under a partial assignment."""
    unassigned = []
    for lit in clause:
        variable = lit_var(lit)
        if variable not in assignment:
            unassigned.append(lit)
        elif assignment[variable] == lit_value(lit):
            return True, []
    return False, unassigned


def resolve(left, right, pivot):
    """Resolve two clauses on a variable and reject tautological resolvents."""
    positive = pivot + 1
    left_set, right_set = set(left), set(right)
    if positive in left_set and -positive in right_set:
        result = (left_set - {positive}) | (right_set - {-positive})
    elif -positive in left_set and positive in right_set:
        result = (left_set - {-positive}) | (right_set - {positive})
    else:
        raise ValueError(("pivot absent with opposite polarity", pivot, left, right))
    return normalize_clause(result)


class CDCL:
    """Deterministic first-variable, false-first CDCL with resolution traces."""

    def __init__(self, nvars, clauses, *, max_decisions=None,
                 max_conflicts=None, max_resolution_steps=None):
        if type(nvars) is not int or nvars < 0:
            raise ValueError("nvars must be a nonnegative integer")
        self.nvars = nvars
        self.input_clauses = []
        self.clauses = []
        for raw in clauses:
            canonical = normalize_clause(raw)
            if canonical is None:
                continue
            if any(abs(lit) > nvars for lit in canonical):
                raise ValueError("literal outside declared variable range")
            self.input_clauses.append(canonical)
            self.clauses.append(canonical)
        self.max_decisions = max_decisions
        self.max_conflicts = max_conflicts
        self.max_resolution_steps = max_resolution_steps
        self.assignment = {}
        self.level = {}
        self.reason = {}
        self.trail = []
        self.trail_limits = []
        self.decision_level = 0
        self.proof = []
        self.stats = {"decisions": 0, "boolean_props": 0, "conflicts": 0,
                      "learned_clauses": 0, "learned_literals": 0,
                      "resolution_steps": 0, "backjumps": 0}

    def assign_lit(self, literal, reason_index):
        variable = lit_var(literal)
        value = lit_value(literal)
        if variable in self.assignment:
            return self.assignment[variable] == value
        self.assignment[variable] = value
        self.level[variable] = self.decision_level
        self.reason[variable] = reason_index
        self.trail.append(variable)
        return True

    def backtrack(self, level):
        if level >= self.decision_level:
            return
        while self.trail and self.level[self.trail[-1]] > level:
            variable = self.trail.pop()
            del self.assignment[variable]
            del self.level[variable]
            del self.reason[variable]
        self.decision_level = level
        self.trail_limits = self.trail_limits[:level]

    def boolean_propagate(self):
        changed = True
        while changed:
            changed = False
            for index, clause in enumerate(self.clauses):
                satisfied, unassigned = clause_state(clause, self.assignment)
                if satisfied:
                    continue
                if not unassigned:
                    return index
                if len(unassigned) == 1:
                    if not self.assign_lit(unassigned[0], index):
                        return index
                    self.stats["boolean_props"] += 1
                    changed = True
        return None

    def analyze(self, conflict_index):
        learned = self.clauses[conflict_index]
        derivation = []
        current = self.decision_level

        def current_count(clause):
            return sum(self.level.get(lit_var(lit), -1) == current for lit in clause)

        while current_count(learned) > 1:
            pivot = None
            for variable in reversed(self.trail):
                if self.level.get(variable, -1) != current:
                    continue
                if (variable + 1 in learned or -(variable + 1) in learned) and \
                        self.reason.get(variable) is not None:
                    pivot = variable
                    break
            if pivot is None:
                raise RuntimeError(("no first-UIP pivot", current, learned, self.trail))
            reason_clause = self.clauses[self.reason[pivot]]
            result = resolve(learned, reason_clause, pivot)
            if result is None:
                raise RuntimeError(("tautological first-UIP resolvent", learned, reason_clause))
            derivation.append({"left": learned, "right": reason_clause,
                               "pivot": pivot, "result": result})
            learned = result
            self.stats["resolution_steps"] += 1
            if (self.max_resolution_steps is not None and
                    self.stats["resolution_steps"] > self.max_resolution_steps):
                return None
        current_literals = [lit for lit in learned
                            if self.level.get(lit_var(lit), -1) == current]
        if current > 0 and len(current_literals) != 1:
            raise RuntimeError(("non-asserting learned clause", current, learned,
                                current_literals))
        back = max((self.level.get(lit_var(lit), 0) for lit in learned
                    if self.level.get(lit_var(lit), -1) != current), default=0)
        return learned, back, derivation

    def derive_empty(self, conflict_index):
        """Resolve a level-zero conflict against its implication reasons."""
        learned = self.clauses[conflict_index]
        derivation = []
        for variable in reversed(self.trail):
            reason_index = self.reason.get(variable)
            if reason_index is None:
                continue
            reason_clause = self.clauses[reason_index]
            if variable + 1 not in learned and -(variable + 1) not in learned:
                continue
            result = resolve(learned, reason_clause, variable)
            if result is None:
                raise RuntimeError(("tautological terminal resolvent", learned, reason_clause))
            derivation.append({"left": learned, "right": reason_clause,
                               "pivot": variable, "result": result})
            learned = result
            self.stats["resolution_steps"] += 1
            if learned == ():
                break
        if learned != ():
            raise RuntimeError(("level-zero conflict did not derive empty clause",
                                learned, self.assignment))
        return derivation

    def decide(self):
        for variable in range(self.nvars):
            if variable not in self.assignment:
                self.decision_level += 1
                self.trail_limits.append(len(self.trail))
                self.assign_lit(-(variable + 1), None)
                self.stats["decisions"] += 1
                return True
        return False

    def _unknown(self, reason):
        return {"status": "UNKNOWN", "model": None, "reason": reason,
                "clauses": [list(c) for c in self.clauses],
                "proof": list(self.proof), "stats": dict(self.stats)}

    def solve(self):
        while True:
            conflict = self.boolean_propagate()
            if conflict is not None:
                self.stats["conflicts"] += 1
                if (self.max_conflicts is not None and
                        self.stats["conflicts"] > self.max_conflicts):
                    return self._unknown("CONFLICT_CAP")
                if self.decision_level == 0:
                    derivation = self.derive_empty(conflict)
                    self.proof.append({"kind": "terminal-empty",
                                       "from_conflict": self.clauses[conflict],
                                       "derivation": derivation})
                    return {"status": "UNSAT", "model": None,
                            "clauses": [list(c) for c in self.clauses],
                            "proof": list(self.proof), "stats": dict(self.stats)}
                analyzed = self.analyze(conflict)
                if analyzed is None:
                    return self._unknown("RESOLUTION_CAP")
                learned, back, derivation = analyzed
                self.proof.append({"kind": "learned", "clause": learned,
                                   "from_conflict": self.clauses[conflict],
                                   "derivation": derivation})
                self.clauses.append(learned)
                self.stats["learned_clauses"] += 1
                self.stats["learned_literals"] += len(learned)
                self.backtrack(back)
                self.stats["backjumps"] += 1
                continue
            if len(self.assignment) == self.nvars:
                return {"status": "SAT", "model": dict(self.assignment),
                        "clauses": [list(c) for c in self.clauses],
                        "proof": list(self.proof), "stats": dict(self.stats)}
            if (self.max_decisions is not None and
                    self.stats["decisions"] >= self.max_decisions):
                return self._unknown("DECISION_CAP")
            if not self.decide():
                raise AssertionError("unassigned variable count disagrees with decision scan")


def source_hashes():
    names = ("cdcl.py", "run_audit.py", "THEOREM.md", "review.py",
             "test_cdcl.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}
