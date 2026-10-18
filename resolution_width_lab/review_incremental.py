"""Independent replay of the incremental bounded-width ladder."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def clause_digest(clauses):
    return hashlib.sha256(
        json.dumps(sorted(clauses), separators=(",", ":")).encode()
    ).hexdigest()


def normalize(clause):
    values = {int(literal) for literal in clause}
    if any(-literal in values for literal in values):
        return None
    return tuple(sorted(values, key=lambda literal: (abs(literal), literal < 0)))


def weakenings(clause, nvars, width):
    present = {abs(literal) for literal in clause}
    missing = [variable for variable in range(1, nvars + 1) if variable not in present]
    for size in range(width - len(clause) + 1):
        for chosen in combinations(missing, size):
            for signs in product((False, True), repeat=size):
                yield normalize(tuple(clause) + tuple(
                    variable if positive else -variable
                    for variable, positive in zip(chosen, signs)))


def resolve(left, right, pivot):
    positive = pivot + 1
    left_set, right_set = set(left), set(right)
    if positive in left_set and -positive in right_set:
        return normalize((left_set - {positive}) | (right_set - {-positive}))
    if -positive in left_set and positive in right_set:
        return normalize((left_set - {-positive}) | (right_set - {positive}))
    raise AssertionError((left, right, pivot))


def closure(nvars, clauses, width, *, seed=(), max_clauses, max_steps):
    known = {tuple(clause) for clause in seed if len(tuple(clause)) <= width}
    queue = sorted(known)
    for raw in clauses:
        clause = normalize(raw)
        if clause is None or len(clause) > width or clause in known:
            continue
        if len(known) >= max_clauses:
            return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                    "clauses": sorted(known), "candidate_steps": 0}
        known.add(clause)
        queue.append(clause)
    if () in known:
        return {"status": "UNSAT", "reason": None,
                "clauses": sorted(known), "candidate_steps": 0}
    steps = 0
    position = 0
    while position < len(queue):
        current = queue[position]
        position += 1
        for weakened in weakenings(current, nvars, width):
            if weakened == current:
                continue
            steps += 1
            if steps > max_steps:
                return {"status": "UNKNOWN", "reason": "STEP_CAP",
                        "clauses": sorted(known), "candidate_steps": steps}
            if weakened not in known:
                if len(known) >= max_clauses:
                    return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                            "clauses": sorted(known), "candidate_steps": steps}
                known.add(weakened)
                queue.append(weakened)
        for other in tuple(sorted(known)):
            for pivot in range(nvars):
                if not ((pivot + 1 in current and -(pivot + 1) in other) or
                        (-(pivot + 1) in current and pivot + 1 in other)):
                    continue
                result = resolve(current, other, pivot)
                if result is None or len(result) > width:
                    continue
                steps += 1
                if steps > max_steps:
                    return {"status": "UNKNOWN", "reason": "STEP_CAP",
                            "clauses": sorted(known), "candidate_steps": steps}
                if result not in known:
                    if len(known) >= max_clauses:
                        return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                                "clauses": sorted(known), "candidate_steps": steps}
                    known.add(result)
                    queue.append(result)
                if result == ():
                    return {"status": "UNSAT", "reason": None,
                            "clauses": sorted(known), "candidate_steps": steps}
    return {"status": "UNKNOWN", "reason": "NO_WIDTH_W_REFUTATION",
            "clauses": sorted(known), "candidate_steps": steps}


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


def expected_case(saved):
    if saved["family"] == "all_assignments":
        return saved["nvars"], all_assignment_clauses(saved["parameter"])
    return pigeonhole(saved["pigeons"], saved["holes"])


def main():
    artifact = json.loads((HERE / "INCREMENTAL_RESULTS.json").read_text(encoding="utf-8"))
    for saved in artifact["rows"]:
        nvars, clauses = expected_case(saved)
        assert nvars == saved["nvars"]
        assert [list(clause) for clause in clauses] == saved["clauses"]
        prior = ()
        for observation in saved["ladder"]:
            width = observation["width"]
            caps = saved["caps"]
            fresh = closure(nvars, clauses, width, max_clauses=caps["max_clauses"],
                            max_steps=caps["max_steps"])
            incremental = closure(nvars, clauses, width, seed=prior,
                                  max_clauses=caps["max_clauses"],
                                  max_steps=caps["max_steps"])
            saved_fresh = observation["baseline"]
            saved_inc = observation["incremental"]
            assert saved_fresh["status"] == fresh["status"]
            assert saved_fresh["reason"] == fresh["reason"]
            assert saved_fresh["closure_size"] == len(fresh["clauses"])
            assert saved_fresh["candidate_steps"] == fresh["candidate_steps"]
            assert saved_fresh["clause_digest"] == clause_digest(fresh["clauses"])
            assert saved_inc["status"] == incremental["status"]
            assert saved_inc["reason"] == incremental["reason"]
            assert saved_inc["closure_size"] == len(incremental["clauses"])
            assert saved_inc["candidate_steps"] == incremental["candidate_steps"]
            assert saved_inc["clause_digest"] == clause_digest(incremental["clauses"])
            assert {tuple(c) for c in fresh["clauses"]} == {tuple(c) for c in incremental["clauses"]}
            assert saved_inc["seed_clauses"] == len(prior)
            if fresh["status"] == "UNKNOWN" and fresh["reason"] == "NO_WIDTH_W_REFUTATION":
                prior = tuple(fresh["clauses"])
            else:
                break
    assert artifact["all_closures_match"]
    expected_hashes = {
        "resolution_width_lab/resolution.py": digest(HERE / "resolution.py"),
        "resolution_width_lab/incremental.py": digest(HERE / "incremental.py"),
        "resolution_width_lab/run_incremental.py": digest(HERE / "run_incremental.py"),
        "resolution_width_lab/review_incremental.py": digest(HERE / "review_incremental.py"),
        "resolution_width_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
    }
    assert artifact["source_sha256"] == expected_hashes
    output = {"status": "PASS", "case_count": len(artifact["rows"]),
              "fresh_and_incremental_closures_match": True,
              "source_hashes_match": True}
    (HERE / "INCREMENTAL_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
