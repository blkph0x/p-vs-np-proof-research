"""Strict, bounded reference checking of text DRUP (RUP additions only).

This is neither a general DRAT/RAT checker nor formally verified software.
Primary format/AT definitions:
https://github.com/marijnheule/drat-trim/blob/master/README.md
https://www.cs.utexas.edu/~marijn/publications/drat-trim.pdf

The original CNF is a multiset. Literal repetition/order is normalized, but
clause multiplicity is retained; deletion removes one occurrence and an
absent deletion is a no-op. Tautologies are retained and have the usual
logical interpretation. Each addition C requires conflict by unit propagation
of the current database under all negated literals of C.

Accepted text is deliberately stricter than general DRAT: one zero-terminated
addition or "d ... 0" deletion per LF/CRLF-terminated line; blank lines and
"c" comment lines are allowed. Integers are canonical ASCII decimal literals
within the original variable bound. All lines, including those after an empty
clause, are processed. An explicit original empty clause permits an empty
proof; unit inconsistency alone does not waive the explicit empty proof step.

Budgets count proof bytes, noncomment steps, literal inspections, and work.
Work charges every proof byte, source clause, proof line, propagation pass,
clause visit, assignment, and decimal digit. A literal inspection additionally
costs 1 + floor(bit_length/64) work units. These are operation counters, not
claims about CPU cycles or a full machine-bit cost model. Budget exhaustion
returns UNKNOWN with no UNSAT claim. Input/proof errors return INVALID.
"""
from __future__ import annotations

from collections import Counter
import re


class _Invalid(ValueError):
    pass


class _Exhausted(Exception):
    pass


def _require(condition, message):
    if not condition:
        raise _Invalid(message)


class _Budget:
    def __init__(self, limits):
        for name, value in limits.items():
            _require(type(value) is int and value >= 0, name + " must be a nonnegative integer")
        self.limits = limits
        self.stats = {
            "proof_bytes": 0, "proof_lines": 0, "steps": 0,
            "input_clauses": 0, "input_literals": 0,
            "additions": 0, "deletions": 0, "absent_deletions": 0,
            "rup_checks": 0, "propagation_passes": 0, "propagations": 0,
            "literal_inspections": 0, "work": 0,
            "active_clauses": 0, "distinct_clauses": 0,
            "peak_active_clauses": 0, "peak_distinct_clauses": 0,
        }

    def reserve(self, field, amount, limit):
        if self.stats[field] + amount > self.limits[limit]:
            raise _Exhausted(limit + " exhausted")
        self.stats[field] += amount

    def work(self, amount=1):
        self.reserve("work", amount, "max_work")

    def literal(self, literal):
        work = 1 + abs(literal).bit_length() // 64
        if self.stats["literal_inspections"] >= self.limits["max_literal_inspections"]:
            raise _Exhausted("max_literal_inspections exhausted")
        self.work(work)
        self.stats["literal_inspections"] += 1

    def step(self):
        if self.stats["steps"] >= self.limits["max_steps"]:
            raise _Exhausted("max_steps exhausted")
        self.work()
        self.stats["steps"] += 1

    def database(self, clauses, total):
        self.stats["active_clauses"] = total
        self.stats["distinct_clauses"] = len(clauses)
        self.stats["peak_active_clauses"] = max(self.stats["peak_active_clauses"], total)
        self.stats["peak_distinct_clauses"] = max(self.stats["peak_distinct_clauses"], len(clauses))


def _canonical(literals):
    return tuple(sorted(set(literals), key=lambda value: (abs(value), value < 0)))


def _formula(nvars, clauses, budget):
    _require(type(nvars) is int and nvars >= 0, "nvars must be a nonnegative exact integer")
    _require(type(clauses) in (list, tuple), "clauses must be an explicit list or tuple")
    database = Counter()
    original_empty = False
    total = 0
    for index, raw in enumerate(clauses):
        budget.work()
        budget.stats["input_clauses"] += 1
        _require(type(raw) in (list, tuple), f"original clause {index} is not a list or tuple")
        values = []
        for literal in raw:
            _require(type(literal) is int and literal != 0 and abs(literal) <= nvars,
                     f"invalid literal in original clause {index}")
            budget.literal(literal)
            budget.stats["input_literals"] += 1
            values.append(literal)
        clause = _canonical(values)
        original_empty |= not clause
        database[clause] += 1
        total += 1
        budget.database(database, total)
    return database, total, original_empty


def _text(proof_text, budget):
    _require(type(proof_text) in (str, bytes), "proof must be str or bytes")
    # Character length is a lower bound on UTF-8 length; reject before allocating
    # an encoded copy when this already exceeds the byte cap.
    if len(proof_text) > budget.limits["max_proof_bytes"]:
        budget.stats["proof_bytes_lower_bound"] = len(proof_text)
        raise _Exhausted("max_proof_bytes exhausted")
    try:
        raw = proof_text.encode("utf-8", errors="strict") if type(proof_text) is str else proof_text
    except UnicodeError as exc:
        raise _Invalid("proof is not valid UTF-8 text") from exc
    budget.stats["proof_bytes"] = len(raw)
    if len(raw) > budget.limits["max_proof_bytes"]:
        raise _Exhausted("max_proof_bytes exhausted")
    budget.work(len(raw))
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise _Invalid("proof is not valid UTF-8 text") from exc
    _require(not text or text.endswith("\n"), "unterminated proof line")
    _require(all(ord(char) >= 32 or char in "\t\r\n" for char in text),
             "unsupported control character in text proof")
    return text


_LITERAL = re.compile(r"-?[1-9][0-9]*\Z")


def _literal(token, nvars, budget):
    _require(_LITERAL.fullmatch(token) is not None, "noncanonical or zero proof literal")
    negative = token.startswith("-")
    value = 0
    for char in token[1:] if negative else token:
        # Range checking during conversion avoids constructing a giant integer
        # for an obviously out-of-range token. Work grows with its intermediate size.
        budget.work(1 + value.bit_length() // 64)
        value = value * 10 + ord(char) - ord("0")
        _require(value <= nvars, "proof literal exceeds original variable bound")
    literal = -value if negative else value
    budget.literal(literal)
    return literal


def _steps(text, nvars, budget):
    for number, raw in enumerate(text.split("\n")[:-1], 1):
        budget.work()
        budget.stats["proof_lines"] += 1
        if raw.endswith("\r"):
            raw = raw[:-1]
        _require("\r" not in raw, f"bare carriage return at line {number}")
        line = raw.strip(" \t")
        if not line or line == "c" or line.startswith(("c ", "c\t")):
            continue
        budget.step()
        fields = re.split("[ \t]+", line)
        deletion = fields[0] == "d"
        if deletion:
            fields = fields[1:]
        _require(bool(fields) and fields[-1] == "0",
                 f"missing final zero at line {number}")
        values = [_literal(token, nvars, budget) for token in fields[:-1]]
        yield deletion, _canonical(values), number


def _rup(clause, database, budget):
    budget.stats["rup_checks"] += 1
    assigned = {}
    for literal in clause:
        budget.literal(literal)
        variable, value = abs(literal), literal < 0
        if variable in assigned and assigned[variable] != value:
            return True
        assigned[variable] = value
    changed = True
    while changed:
        budget.work()
        budget.stats["propagation_passes"] += 1
        changed = False
        # Multiplicity matters for deletion, but identical clauses need only
        # one scan during unit propagation.
        for active in database:
            budget.work()
            satisfied = False
            unassigned = 0
            last = None
            for literal in active:
                budget.literal(literal)
                value = assigned.get(abs(literal))
                if value is None:
                    unassigned += 1
                    last = literal
                elif value == (literal > 0):
                    satisfied = True
                    break
            if satisfied:
                continue
            if unassigned == 0:
                return True
            if unassigned == 1:
                budget.work()
                assigned[abs(last)] = last > 0
                budget.stats["propagations"] += 1
                changed = True
    return False


def verify_rup(nvars, clauses, proof_text, *, max_steps=100000,
               max_literal_inspections=10000000, max_proof_bytes=10000000,
               max_work=10000000):
    """Return VERIFIED only for a complete strict DRUP refutation of this CNF."""
    budget = None
    try:
        budget = _Budget({
            "max_steps": max_steps, "max_literal_inspections": max_literal_inspections,
            "max_proof_bytes": max_proof_bytes, "max_work": max_work,
        })
        database, total, complete = _formula(nvars, clauses, budget)
        text = _text(proof_text, budget)
        original_empty = complete
        for deletion, clause, line in _steps(text, nvars, budget):
            if deletion:
                budget.stats["deletions"] += 1
                if database.get(clause, 0):
                    database[clause] -= 1
                    total -= 1
                    if database[clause] == 0:
                        del database[clause]
                else:
                    budget.stats["absent_deletions"] += 1
            else:
                _require(_rup(clause, database, budget), f"addition at line {line} is not RUP")
                database[clause] += 1
                total += 1
                budget.stats["additions"] += 1
                complete |= not clause
            budget.database(database, total)
        _require(complete, "proof has no validated empty addition or original empty clause")
        return {
            "valid": True, "status": "VERIFIED", "claim": "UNSAT", "errors": [],
            "method": "strict text DRUP with forward RUP checks; no RAT fallback",
            "completion": "original_empty_clause" if original_empty else "validated_empty_addition",
            "stats": dict(budget.stats),
        }
    except _Exhausted as exc:
        return {"valid": False, "status": "UNKNOWN", "claim": None,
                "errors": [str(exc)], "stats": dict(budget.stats) if budget else {}}
    except (_Invalid, TypeError, ValueError, UnicodeError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "claim": None,
                "errors": [str(exc)], "stats": dict(budget.stats) if budget else {}}
