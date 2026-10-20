"""Independent verifier for general-CDCL models, clauses, and resolution traces."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


class VerificationError(ValueError):
    """A certificate failed an explicit, optimization-independent check."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def normalize(clause):
    require(type(clause) in (list, tuple), "clause must be a list or tuple")
    require(all(type(lit) is int and lit != 0 for lit in clause),
            "clause literals must be nonzero exact integers")
    values = set(clause)
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, pivot):
    p = pivot + 1
    a, b = set(left), set(right)
    if p in a and -p in b:
        result = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        result = (a - {-p}) | (b - {p})
    else:
        raise VerificationError("resolution pivot lacks opposite polarities")
    return normalize(tuple(result))


def clause_satisfied(clause, assignment):
    return any(assignment[abs(lit) - 1] == (lit > 0) for lit in clause)


def direct(nvars, clauses):
    return any(all(clause_satisfied(clause, assignment) for clause in clauses)
               for assignment in product((False, True), repeat=nvars))


def replay(nvars, clauses, result):
    """Check a proof/model against the supplied original CNF.

    No exhaustive SAT oracle or Python assert is part of acceptance. Runtime
    counters and the historical reason for an UNKNOWN are not authenticated.
    """
    require(type(nvars) is int and nvars >= 0, "invalid variable count")
    require(type(clauses) in (list, tuple), "original clauses must be a sequence")
    require(type(result) is dict, "result must be a dictionary")
    require(result.get("status") in ("SAT", "UNSAT", "UNKNOWN"),
            "unknown result status")
    require(type(result.get("proof")) is list, "proof must be a list")

    def checked_clause(raw, *, canonical=False):
        clause = normalize(raw)
        require(all(abs(lit) <= nvars for lit in raw),
                "literal outside original variable range")
        if canonical:
            require(clause is not None and tuple(raw) == clause,
                    "proof clauses must be canonical and non-tautological")
        return clause

    database = []
    for clause in clauses:
        canonical = checked_clause(clause)
        if canonical is not None:
            database.append(canonical)
    known = set(database)
    terminal_seen = False
    for event_index, event in enumerate(result["proof"]):
        require(type(event) is dict, "proof event must be a dictionary")
        kind = event.get("kind")
        require(kind in ("learned", "terminal-empty"), "invalid proof event kind")
        current = checked_clause(event.get("from_conflict"), canonical=True)
        require(current in known, "conflict clause is not an available parent")
        require(type(event.get("derivation")) is list, "derivation must be a list")
        for step in event["derivation"]:
            require(type(step) is dict, "resolution step must be a dictionary")
            require(checked_clause(step.get("left"), canonical=True) == current,
                    "resolution left parent is not the current clause")
            right = checked_clause(step.get("right"), canonical=True)
            require(right in known, "resolution right parent is unavailable")
            pivot = step.get("pivot")
            require(type(pivot) is int and 0 <= pivot < nvars, "invalid pivot")
            derived = resolve(current, right, pivot)
            require(derived is not None, "tautological resolution conclusion")
            require(derived == checked_clause(step.get("result"), canonical=True),
                    "incorrect resolution conclusion")
            current = derived
        if kind == "learned":
            require(current == checked_clause(event.get("clause"), canonical=True),
                    "learned clause differs from its derivation")
            database.append(current)
            known.add(current)
        else:
            require(current == (), "terminal event did not derive the empty clause")
            require(event_index == len(result["proof"]) - 1,
                    "terminal empty-clause event must be last")
            terminal_seen = True
    require(type(result.get("clauses")) is list, "reported database must be a list")
    reported = [checked_clause(c, canonical=True) for c in result["clauses"]]
    require(reported == database, "reported database differs from replay")
    if result["status"] == "SAT":
        require(not terminal_seen, "SAT result contains a contradiction")
        model = result.get("model")
        require(type(model) is dict, "SAT model must be a dictionary")
        assignment = {}
        for key, value in model.items():
            if type(key) is int:
                variable = key
            elif type(key) is str and key.isascii() and key.isdecimal():
                variable = int(key)
                require(str(variable) == key, "noncanonical model variable")
            else:
                raise VerificationError("invalid model variable")
            require(0 <= variable < nvars and variable not in assignment,
                    "duplicate or out-of-range model variable")
            require(type(value) is bool, "model values must be Boolean")
            assignment[variable] = value
        require(len(assignment) == nvars, "incomplete SAT model")
        require(all(clause_satisfied(clause, assignment) for clause in clauses),
                "model falsifies an original clause")
    elif result["status"] == "UNSAT":
        require(result.get("model") is None, "UNSAT must not supply a model")
        require(terminal_seen, "UNSAT requires a terminal empty-clause proof")
    else:
        require(result.get("model") is None and not terminal_seen,
                "UNKNOWN must not contain a claimed completed result")
        require(result.get("reason") in ("DECISION_CAP", "CONFLICT_CAP", "RESOLUTION_CAP"),
                "invalid UNKNOWN reason")
    return True


def main():
    artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8"))
    for saved in certificates:
        replay(saved["nvars"], saved["clauses"], saved["result"])
    require(artifact.get("all_cases_match_direct") is True,
            "saved finite oracle campaign did not pass")
    for name, digest in artifact["source_sha256"].items():
        require(sha256((HERE / name).read_bytes()).hexdigest() == digest,
                "source hash mismatch: " + name)
    output = {"status": "PASS", "case_count": len(certificates),
              "proofs_match": True, "source_hashes_match": True}
    (HERE / "REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
