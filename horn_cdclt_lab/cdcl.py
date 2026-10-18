"""A small proof-producing CDCL(T) engine for the Horn/affine portfolio.

The Boolean database contains only theory lemmas and learned clauses.  Horn clauses
and affine equations remain opaque to the SAT layer; every exposed explanation carries
an independently replayable source certificate.  This keeps the experiment honest:
clause learning can be measured without silently replacing the mixed theory by a
pre-expanded CNF.
"""
from __future__ import annotations

from engine import (AffineTheory, HornTheory, MixedPortfolioSolver, clause_state,
                    lit_value, lit_var)


def normalize_clause(clause):
    s = set(int(x) for x in clause)
    if any(-x in s for x in s):
        return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def lit_for(var, value):
    return var + 1 if value else -(var + 1)


def unit_or_conflict(clause, assignment):
    satisfied, unassigned = clause_state(clause, assignment)
    if satisfied:
        return "sat", None
    if not unassigned:
        return "conflict", None
    if len(unassigned) == 1:
        return "unit", unassigned[0]
    return "open", None


def resolve(left, right, pivot):
    p = pivot + 1
    a = set(left)
    b = set(right)
    if p in a and -p in b:
        out = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        out = (a - {-p}) | (b - {p})
    else:
        raise ValueError(("bad pivot", pivot, left, right))
    return normalize_clause(out)


def affine_clause(theory, cert):
    mask, _ = theory.combined(cert["combo"])
    assignment = cert["assignment"]
    if cert["kind"] == "affine-conflict":
        return normalize_clause(
            [lit_for(v, not assignment[v]) for v in range(mask.bit_length())
             if (mask >> v) & 1])
    if cert["kind"] == "affine-prop":
        pv = cert["var"]
        lits = [lit_for(pv, cert["value"])]
        for v in range(mask.bit_length()):
            if v == pv or not ((mask >> v) & 1):
                continue
            lits.append(lit_for(v, not assignment[v]))
        return normalize_clause(lits)
    raise ValueError(cert)


class CDCLMixed:
    """Deterministic first-variable, false-first CDCL(T) with first-UIP learning."""

    def __init__(self, nvars, horn=None, affine=None, initial_clauses=()):
        self.nvars = int(nvars)
        self.horn = horn
        self.affine = affine
        self.clauses = []
        self.assign = {}
        self.level = {}
        self.reason = {}
        self.trail = []
        self.trail_lim = []
        self.decision_level = 0
        self.proof = []
        self.stats = {
            "decisions": 0, "boolean_props": 0, "theory_props": 0,
            "conflicts": 0, "theory_lemmas": 0, "learned_clauses": 0,
            "learned_literals": 0, "resolution_steps": 0, "backjumps": 0,
            "certificates_verified": 0,
        }
        for clause in initial_clauses:
            self.add_clause(clause, {"kind": "initial", "clause": normalize_clause(clause)})

    def add_clause(self, clause, proof_entry=None):
        clause = normalize_clause(clause)
        if clause is None:
            return None
        idx = len(self.clauses)
        self.clauses.append(clause)
        if proof_entry is not None:
            entry = dict(proof_entry)
            entry["clause"] = clause
            self.proof.append(entry)
        return idx

    def assign_lit(self, lit, reason_idx):
        v = lit_var(lit)
        value = lit_value(lit)
        if v in self.assign:
            return self.assign[v] == value
        self.assign[v] = value
        self.level[v] = self.decision_level
        self.reason[v] = reason_idx
        self.trail.append(v)
        return True

    def backtrack(self, level):
        if level >= self.decision_level:
            return
        while self.trail and self.level[self.trail[-1]] > level:
            v = self.trail.pop()
            del self.assign[v]
            del self.level[v]
            del self.reason[v]
        self.decision_level = level
        self.trail_lim = self.trail_lim[:level]

    def boolean_propagate(self):
        changed = True
        while changed:
            changed = False
            for idx, clause in enumerate(self.clauses):
                state, lit = unit_or_conflict(clause, self.assign)
                if state == "conflict":
                    return idx
                if state == "unit":
                    if not self.assign_lit(lit, idx):
                        return idx
                    self.stats["boolean_props"] += 1
                    changed = True
        return None

    def _add_theory_lemma(self, theory_name, cert):
        theory = self.horn if theory_name == "horn" else self.affine
        assert theory is not None and theory.verify(cert)
        self.stats["certificates_verified"] += 1
        if theory_name == "horn":
            clause = theory.clause(cert)
        else:
            clause = affine_clause(theory, cert)
        clause = normalize_clause(clause)
        assert clause is not None
        idx = self.add_clause(clause, {"kind": "theory", "theory": theory_name,
                                       "certificate": cert})
        self.stats["theory_lemmas"] += 1
        return idx, clause

    def theory_step(self):
        if self.horn:
            props, conflict = self.horn.analyze(self.assign)
            if conflict:
                idx, _ = self._add_theory_lemma("horn", conflict)
                return "conflict", idx
            if props:
                v, value, cert = props[0]
                idx, clause = self._add_theory_lemma("horn", cert)
                lit = lit_for(v, value)
                state, unit = unit_or_conflict(clause, self.assign)
                assert state == "unit" and unit == lit
                assert self.assign_lit(lit, idx)
                self.stats["theory_props"] += 1
                return "prop", None
        if self.affine:
            props, conflict = self.affine.analyze(self.assign)
            if conflict:
                idx, _ = self._add_theory_lemma("affine", conflict)
                return "conflict", idx
            if props:
                v, value, cert = props[0]
                idx, clause = self._add_theory_lemma("affine", cert)
                lit = lit_for(v, value)
                state, unit = unit_or_conflict(clause, self.assign)
                assert state == "unit" and unit == lit
                assert self.assign_lit(lit, idx)
                self.stats["theory_props"] += 1
                return "prop", None
        return "none", None

    def propagate(self):
        while True:
            conflict = self.boolean_propagate()
            if conflict is not None:
                return conflict
            kind, idx = self.theory_step()
            if kind == "conflict":
                return idx
            if kind == "prop":
                continue
            return None

    def analyze(self, conflict_idx):
        learned = self.clauses[conflict_idx]
        steps = []
        current = self.decision_level

        def current_count(clause):
            return sum(self.level.get(lit_var(lit), -1) == current for lit in clause)

        while current_count(learned) > 1:
            pivot = None
            for v in reversed(self.trail):
                if self.level.get(v, -1) != current:
                    continue
                if (v + 1 in learned or -(v + 1) in learned) and self.reason.get(v) is not None:
                    pivot = v
                    break
            if pivot is None:
                raise RuntimeError(("no first-UIP pivot", current, learned, self.trail))
            reason_idx = self.reason[pivot]
            reason = self.clauses[reason_idx]
            out = resolve(learned, reason, pivot)
            if out is None:
                raise RuntimeError(("tautological resolution", learned, reason, pivot))
            step = {"kind": "resolve", "left": learned, "right": reason,
                    "pivot": pivot, "result": out}
            steps.append(step)
            learned = out

        current_lits = [lit for lit in learned
                        if self.level.get(lit_var(lit), -1) == current]
        if current > 0 and len(current_lits) != 1:
            raise RuntimeError(("non-asserting learned clause", current, learned, current_lits))
        back = max((self.level.get(lit_var(lit), 0) for lit in learned
                    if self.level.get(lit_var(lit), -1) != current), default=0)
        return learned, back, steps

    def decide(self):
        for v in range(self.nvars):
            if v not in self.assign:
                self.decision_level += 1
                self.trail_lim.append(len(self.trail))
                assert self.assign_lit(lit_for(v, False), None)
                self.stats["decisions"] += 1
                return True
        return False

    def solve(self):
        while True:
            conflict = self.propagate()
            if conflict is not None:
                self.stats["conflicts"] += 1
                if self.decision_level == 0:
                    self.proof.append({"kind": "terminal-conflict",
                                       "clause": self.clauses[conflict],
                                       "assignment": dict(self.assign)})
                    return None
                learned, back, steps = self.analyze(conflict)
                for step in steps:
                    self.proof.append(step)
                    self.stats["resolution_steps"] += 1
                self.add_clause(learned, {"kind": "learned",
                                          "from_conflict": self.clauses[conflict],
                                          "derivation": steps})
                self.stats["learned_clauses"] += 1
                self.stats["learned_literals"] += len(learned)
                self.backtrack(back)
                self.stats["backjumps"] += 1
                continue
            if len(self.assign) == self.nvars:
                return dict(self.assign)
            if not self.decide():
                return dict(self.assign)


def solve_encoded(clauses):
    """Convenience wrapper for the fixed two-bridge exact-one reduction."""
    # Imported lazily to keep this module's core independent of the gadget constructor.
    from engine import encode_exact_one
    n, horn, affine = encode_exact_one(clauses)
    solver = CDCLMixed(n, horn=horn, affine=affine)
    return solver, solver.solve()

