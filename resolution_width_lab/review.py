"""Independent closure and proof replay for bounded-width resolution."""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def normalize(clause):
    values = {int(lit) for lit in clause}
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, pivot):
    p = pivot + 1
    a, b = set(left), set(right)
    if p in a and -p in b:
        out = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        out = (a - {-p}) | (b - {p})
    else:
        raise AssertionError((left, right, pivot))
    return normalize(out)


def weakenings(clause, nvars, width):
    present = {abs(lit) for lit in clause}
    missing = [v for v in range(1, nvars + 1) if v not in present]
    for size in range(width - len(clause) + 1):
        for chosen in combinations(missing, size):
            for signs in product((False, True), repeat=size):
                yield normalize(tuple(clause) + tuple(
                    v if sign else -v for v, sign in zip(chosen, signs)))


def closure(nvars, clauses, width, max_clauses, max_steps):
    original = [normalize(c) for c in clauses]
    initial = [c for c in original if c is not None and len(c) <= width]
    known, queue, records = set(), list(), []

    def add(c, record):
        if c in known:
            return True
        if len(known) >= max_clauses:
            return False
        known.add(c); queue.append(c); records.append(record)
        return True

    for c in initial:
        if not add(c, {"kind": "axiom", "clause": c}):
            return None, records, "CLAUSE_CAP"
    steps = 0
    position = 0
    while position < len(queue):
        current = queue[position]; position += 1
        candidates = []
        for weakened in weakenings(current, nvars, width):
            if weakened != current:
                candidates.append((weakened, {"kind": "weaken",
                                              "parent": current, "clause": weakened}))
        for other in tuple(sorted(known)):
            for pivot in range(nvars):
                if ((pivot + 1 in current and -(pivot + 1) in other) or
                        (-(pivot + 1) in current and pivot + 1 in other)):
                    result = resolve(current, other, pivot)
                    if result is not None and len(result) <= width:
                        candidates.append((result, {"kind": "resolve", "left": current,
                                                     "right": other, "pivot": pivot,
                                                     "clause": result}))
        for result, record in candidates:
            steps += 1
            if steps > max_steps:
                return None, records, "STEP_CAP"
            if result not in known and not add(result, record):
                return None, records, "CLAUSE_CAP"
            if result == ():
                return known, records, None
    return known, records, "NO_WIDTH_W_REFUTATION"


def width_sweep(nvars, clauses, max_clauses=10000, max_steps=100000):
    """Independently recompute the first refutation width and statuses."""
    max_width = max((len(clause) for clause in clauses), default=0)
    observations = []
    for width in range(max_width + 1):
        known, _, reason = closure(nvars, clauses, width, max_clauses, max_steps)
        capped = reason in {"CLAUSE_CAP", "STEP_CAP"}
        status = "UNSAT" if known is not None and () in known else "UNKNOWN"
        observations.append({"width": width, "status": status,
                            "reason": None if status == "UNSAT" else reason,
                            "closure_size": None if known is None else len(known)})
        if status == "UNSAT":
            return width, observations
        if capped:
            return None, observations
    return None, observations


def replay_proof(clauses, proof):
    known = set()
    for event in proof:
        if event["kind"] == "axiom":
            clause = tuple(event["clause"])
            assert normalize(clause) == clause
            known.add(clause)
        elif event["kind"] == "weaken":
            parent, clause = tuple(event["parent"]), tuple(event["clause"])
            assert parent in known and set(parent).issubset(clause)
            assert normalize(clause) == clause
            known.add(clause)
        elif event["kind"] == "resolve":
            left, right = tuple(event["left"]), tuple(event["right"])
            assert left in known and right in known
            result = resolve(left, right, int(event["pivot"]))
            assert result == tuple(event["clause"])
            known.add(result)
        else:
            raise AssertionError(event)
    return known


def main():
    artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8"))
    for saved in certificates:
        result = saved["result"]
        caps = saved["caps"]
        max_clauses, max_steps = caps.get("max_clauses", 10000), caps.get("max_steps", 100000)
        expected, _, reason = closure(saved["nvars"], saved["clauses"], saved["width"],
                                      max_clauses, max_steps)
        if result["status"] == "UNSAT":
            replayed = replay_proof(saved["clauses"], result["proof"])
            assert () in replayed and () in expected
            assert replayed == {tuple(clause) for clause in result["clauses"]}
            assert replayed.issubset(expected)
        elif result["reason"] == "NO_WIDTH_W_REFUTATION":
            assert expected is not None and () not in expected
            assert {tuple(clause) for clause in result["clauses"]} == expected
        else:
            assert result["reason"] == reason
        if not caps:
            minimum, sweep = width_sweep(saved["nvars"], saved["clauses"])
            assert minimum == saved["minimum_refutation_width"]
            saved_sweep = saved["width_sweep"]
            assert [(row["width"], row["status"], row["reason"])
                    for row in saved_sweep] == [
                        (row["width"], row["status"], row["reason"])
                        for row in sweep]
            assert saved_sweep[-1]["width"] == sweep[-1]["width"]
    assert artifact["all_cases_replayed"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(certificates),
              "closures_match": True, "proofs_match": True,
              "source_hashes_match": True}
    (HERE / "REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
