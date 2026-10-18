"""Independent replay of the indexed width stress artifact."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def normalize(clause):
    values = {int(lit) for lit in clause}
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, literal):
    a, b = set(left), set(right)
    if literal in a and -literal in b:
        return normalize((a - {literal}) | (b - {-literal}))
    if -literal in a and literal in b:
        return normalize((a - {-literal}) | (b - {literal}))
    raise AssertionError((left, right, literal))


def weakenings(clause, nvars, width):
    present = {abs(lit) for lit in clause}
    missing = [variable for variable in range(1, nvars + 1) if variable not in present]
    for size in range(width - len(clause) + 1):
        for chosen in combinations(missing, size):
            for signs in product((False, True), repeat=size):
                yield normalize(tuple(clause) + tuple(
                    variable if positive else -variable
                    for variable, positive in zip(chosen, signs)
                ))


def closure(nvars, clauses, width, seed, max_clauses, max_steps):
    known, queue, by_literal = set(), [], {}
    stats = {"candidate_steps": 0, "weakening_steps": 0,
             "resolution_steps": 0, "indexed_resolution_pairs": 0}

    def add(clause):
        if clause in known:
            return True
        if len(known) >= max_clauses:
            return False
        known.add(clause)
        queue.append(clause)
        for literal in clause:
            by_literal.setdefault(literal, set()).add(clause)
        return True

    for raw in sorted(seed):
        clause = normalize(raw)
        if clause is not None and len(clause) <= width and not add(clause):
            return "UNKNOWN", "CLAUSE_CAP", known, stats
    for raw in clauses:
        clause = normalize(raw)
        if clause is not None and len(clause) <= width and not add(clause):
            return "UNKNOWN", "CLAUSE_CAP", known, stats
    if () in known:
        return "UNSAT", None, known, stats

    position = 0
    while position < len(queue):
        current = queue[position]
        position += 1
        for weakened in weakenings(current, nvars, width):
            if weakened == current:
                continue
            stats["candidate_steps"] += 1
            stats["weakening_steps"] += 1
            if stats["candidate_steps"] > max_steps:
                return "UNKNOWN", "STEP_CAP", known, stats
            if not add(weakened):
                return "UNKNOWN", "CLAUSE_CAP", known, stats
        for literal in current:
            for other in sorted(by_literal.get(-literal, ())):
                stats["indexed_resolution_pairs"] += 1
                result = resolve(current, other, literal)
                if result is None or len(result) > width:
                    continue
                stats["candidate_steps"] += 1
                stats["resolution_steps"] += 1
                if stats["candidate_steps"] > max_steps:
                    return "UNKNOWN", "STEP_CAP", known, stats
                if not add(result):
                    return "UNKNOWN", "CLAUSE_CAP", known, stats
                if result == ():
                    return "UNSAT", None, known, stats
    return "UNKNOWN", "NO_WIDTH_W_REFUTATION", known, stats


def all_assignment_clauses(nvars):
    return tuple(tuple((variable + 1) if not bit else -(variable + 1)
                       for variable, bit in enumerate(bits))
                 for bits in product((0, 1), repeat=nvars))


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    clauses += [(-variable(pigeon, left), -variable(pigeon, right))
                for pigeon in range(pigeons)
                for left, right in combinations(range(holes), 2)]
    clauses += [(-variable(left, hole), -variable(right, hole))
                for hole in range(holes)
                for left, right in combinations(range(pigeons), 2)]
    return pigeons * holes, tuple(clauses)


def case(name):
    if name.startswith("all_assignments_n"):
        nvars = int(name.rsplit("n", 1)[1])
        return nvars, all_assignment_clauses(nvars)
    if name.startswith("pigeonhole_"):
        pigeons, holes = (int(value) for value in name.removeprefix("pigeonhole_").split("_"))
        return pigeonhole(pigeons, holes)
    raise AssertionError(name)


def compact_digest(clauses):
    payload = json.dumps(sorted(clauses), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def compare(row, status, reason, known, stats):
    assert row["status"] == status, (row["name"], row["status"], status)
    assert row["reason"] == reason, (row["name"], row["reason"], reason)
    assert row["closure_size"] == len(known), row["name"]
    assert row["clause_digest"] == compact_digest(known), row["name"]


def main():
    artifact = json.loads((HERE / "INDEXED_RESULTS.json").read_text(encoding="utf-8"))
    for relative, expected in artifact["source_sha256"].items():
        assert digest(HERE / relative.split("/", 1)[1]) == expected, relative

    rows = artifact["rows"]
    seed = ()
    for row in rows:
        if row["name"] == "pigeonhole_5_4":
            break
        nvars, clauses = case(row["name"])
        status, reason, known, stats = closure(
            nvars, clauses, row["width"], seed,
            artifact["caps"]["max_clauses"], artifact["caps"]["max_steps"],
        )
        compare(row, status, reason, known, stats)
        if status == "UNKNOWN" and reason == "NO_WIDTH_W_REFUTATION":
            seed = tuple(sorted(known))
        else:
            seed = ()

    stress_nvars, stress_clauses = pigeonhole(5, 4)
    width3 = next(row for row in rows if row["name"] == "pigeonhole_5_4" and row["width"] == 3)
    status, reason, known, stats = closure(
        stress_nvars, stress_clauses, 3, (),
        artifact["caps"]["max_clauses"], artifact["caps"]["max_steps"],
    )
    compare(width3, status, reason, known, stats)
    width4 = next(row for row in rows if row["name"] == "pigeonhole_5_4" and row["width"] == 4)
    status, reason, known, stats = closure(
        stress_nvars, stress_clauses, 4, tuple(sorted(known)),
        artifact["caps"]["max_clauses"], artifact["caps"]["max_steps"],
    )
    assert status == "UNKNOWN" and reason == "STEP_CAP"
    assert stats["candidate_steps"] > artifact["caps"]["max_steps"]
    assert width4["status"] == status and width4["reason"] == reason
    output = {"status": "PASS", "rows_replayed": len(rows),
              "exact_rows_match": True, "stress_cap_replayed": True,
              "source_hashes_match": True}
    (HERE / "INDEXED_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
