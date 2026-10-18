"""Independent replay for the CDCL(T) proof log.

This file intentionally does not call CDCLMixed's verifier or resolution routine.  It
recomputes source explanations, Gaussian row combinations, and every recorded resolution
step from the serialized proof events.
"""
from __future__ import annotations

from engine import parity


def norm(clause):
    s = set(int(x) for x in clause)
    if any(-x in s for x in s):
        return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def lit_var(lit):
    return abs(lit) - 1


def clause_state(clause, assignment):
    unassigned = []
    for lit in clause:
        v = lit_var(lit)
        if v not in assignment:
            unassigned.append(lit)
        elif assignment[v] == (lit > 0):
            return True, []
    return False, unassigned


def replay_horn(clauses, cert):
    if cert.get("kind") not in {"horn-prop", "horn-conflict"}:
        return False
    i = cert.get("clause_index")
    if not isinstance(i, int) or not 0 <= i < len(clauses):
        return False
    clause = clauses[i]
    assignment = cert.get("assignment")
    if not isinstance(assignment, dict):
        return False
    satisfied, unassigned = clause_state(clause, assignment)
    if satisfied:
        return False
    if cert["kind"] == "horn-conflict":
        return not unassigned
    return len(unassigned) == 1 and unassigned[0] == cert.get("lit")


def combined(equations, combo):
    mask = rhs = 0
    for i, (m, r) in enumerate(equations):
        if (combo >> i) & 1:
            mask ^= m
            rhs ^= r
    return mask, rhs


def affine_explanation(equations, cert):
    if cert.get("kind") not in {"affine-prop", "affine-conflict"}:
        return None
    combo = cert.get("combo")
    if not isinstance(combo, int) or combo < 0 or combo >= (1 << len(equations)):
        return None
    assignment = cert.get("assignment")
    if not isinstance(assignment, dict):
        return None
    mask, rhs = combined(equations, combo)
    assigned_mask = sum(1 << v for v in assignment)
    bits = sum(1 << v for v, value in assignment.items() if value)
    residual_mask = mask & ~assigned_mask
    residual_rhs = rhs ^ parity(mask & bits)
    if cert["kind"] == "affine-conflict":
        if residual_mask != 0 or residual_rhs != 1:
            return None
        return norm([(-(v + 1) if assignment[v] else (v + 1))
                     for v in range(mask.bit_length()) if (mask >> v) & 1])
    var = cert.get("var")
    if not isinstance(var, int) or var in assignment:
        return None
    if residual_mask != (1 << var) or residual_rhs != int(cert.get("value")):
        return None
    lits = [var + 1 if cert["value"] else -(var + 1)]
    lits.extend((-(v + 1) if assignment[v] else (v + 1))
                for v in range(mask.bit_length())
                if v != var and ((mask >> v) & 1))
    return norm(lits)


def replay_resolution(left, right, pivot):
    p = pivot + 1
    a = set(left)
    b = set(right)
    if p in a and -p in b:
        out = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        out = (a - {-p}) | (b - {p})
    else:
        return None
    return norm(out)


def replay_solver(solver):
    """Return a structured independent verdict for a completed CDCL run."""
    db = []
    events_ok = []
    for event in solver.proof:
        kind = event.get("kind")
        if kind == "initial":
            clause = norm(event.get("clause", ()))
            ok = clause is not None and clause == event.get("clause")
            if ok:
                db.append(clause)
            events_ok.append(ok)
            continue
        if kind == "theory":
            cert = event.get("certificate", {})
            if event.get("theory") == "horn" and solver.horn:
                i = cert.get("clause_index")
                expected = (norm(solver.horn.clauses[i])
                            if isinstance(i, int) and 0 <= i < len(solver.horn.clauses)
                            else None)
                ok = replay_horn(solver.horn.clauses, cert) and expected == event.get("clause")
            elif event.get("theory") == "affine" and solver.affine:
                expected = affine_explanation(solver.affine.equations, cert)
                ok = expected is not None and expected == event.get("clause")
            else:
                ok = False
            if ok:
                db.append(event["clause"])
            events_ok.append(ok)
            continue
        if kind == "resolve":
            left = event.get("left")
            right = event.get("right")
            result = replay_resolution(left, right, event.get("pivot"))
            events_ok.append(result == event.get("result"))
            continue
        if kind == "learned":
            conflict = event.get("from_conflict")
            ok = conflict in db
            current = conflict
            for step in event.get("derivation", ()):
                if step.get("left") != current or step.get("right") not in db:
                    ok = False
                    break
                current = replay_resolution(current, step["right"], step.get("pivot"))
                if current is None or current != step.get("result"):
                    ok = False
                    break
            ok = ok and current == event.get("clause")
            if ok:
                db.append(event["clause"])
            events_ok.append(ok)
            continue
        if kind == "terminal-conflict":
            clause = event.get("clause")
            assignment = event.get("assignment", {})
            satisfied, unassigned = clause_state(clause, assignment)
            events_ok.append(clause in db and not satisfied and not unassigned)
            continue
        events_ok.append(False)
    return {
        "events": len(events_ok),
        "all_events_valid": all(events_ok),
        "database_clauses_replayed": len(db),
        "solver_clauses": len(solver.clauses),
        "database_size_matches": len(db) == len(solver.clauses),
    }

