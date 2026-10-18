"""Independent replay of the finite width/frontier/CDCL bridge."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode()).hexdigest()


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
                    for variable, positive in zip(chosen, signs)
                ))


def resolve(left, right, pivot):
    positive = pivot + 1
    left_set, right_set = set(left), set(right)
    if positive in left_set and -positive in right_set:
        return normalize((left_set - {positive}) | (right_set - {-positive}))
    if -positive in left_set and positive in right_set:
        return normalize((left_set - {-positive}) | (right_set - {positive}))
    raise AssertionError((left, right, pivot))


def closure(nvars, clauses, width, max_clauses, max_steps):
    initial = [normalize(clause) for clause in clauses]
    initial = [clause for clause in initial if clause is not None and len(clause) <= width]
    known, queue = set(), []

    def add(clause):
        if clause in known:
            return True
        if len(known) >= max_clauses:
            return False
        known.add(clause)
        queue.append(clause)
        return True

    for clause in initial:
        if not add(clause):
            return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                    "closure_size": len(known), "candidate_steps": 0,
                    "contains_empty": () in known}
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
                        "closure_size": len(known), "candidate_steps": steps,
                        "contains_empty": () in known}
            if weakened not in known and not add(weakened):
                return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                        "closure_size": len(known), "candidate_steps": steps,
                        "contains_empty": () in known}
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
                            "closure_size": len(known), "candidate_steps": steps,
                            "contains_empty": () in known}
                if result not in known and not add(result):
                    return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                            "closure_size": len(known), "candidate_steps": steps,
                            "contains_empty": () in known}
                if result == ():
                    return {"status": "UNSAT", "reason": None,
                            "closure_size": len(known), "candidate_steps": steps,
                            "contains_empty": True}
    return {"status": "UNKNOWN", "reason": "NO_WIDTH_W_REFUTATION",
            "closure_size": len(known), "candidate_steps": steps,
            "contains_empty": () in known}


def all_assignment_clauses(nvars):
    return tuple(
        tuple((variable + 1) if not bit else -(variable + 1)
              for variable, bit in enumerate(bits))
        for bits in product((0, 1), repeat=nvars)
    )


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [
        tuple(variable(pigeon, hole) for hole in range(holes))
        for pigeon in range(pigeons)
    ]
    clauses += [
        (-variable(pigeon, left), -variable(pigeon, right))
        for pigeon in range(pigeons)
        for left, right in combinations(range(holes), 2)
    ]
    clauses += [
        (-variable(left, hole), -variable(right, hole))
        for hole in range(holes)
        for left, right in combinations(range(pigeons), 2)
    ]
    return pigeons * holes, tuple(clauses)


def expected_case(saved):
    if saved["family"] == "all_assignments":
        return saved["nvars"], all_assignment_clauses(saved["parameter"])
    return pigeonhole(saved["pigeons"], saved["holes"])


def main():
    artifact = json.loads((HERE / "WIDTH_RESULTS.json").read_text(encoding="utf-8"))
    scaling = json.loads(
        (ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json")
        .read_text(encoding="utf-8")
    )
    scaling_by_name = {row["name"]: row for row in scaling["rows"]}
    frontier = json.loads((HERE / "FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
    frontier_by_name = {row["name"]: row for row in frontier["rows"]}
    expected_widths = {
        "all_assignments_n1": 1,
        "all_assignments_n2": 2,
        "all_assignments_n3": 3,
        "all_assignments_n4": 4,
        "pigeonhole_2_1": 2,
        "pigeonhole_3_2": 2,
        "pigeonhole_4_3": 3,
    }
    for saved in artifact["rows"]:
        nvars, clauses = expected_case(saved)
        assert nvars == saved["nvars"]
        assert [list(clause) for clause in clauses] == saved["clauses"]
        assert len(clauses) == saved["clause_count"]
        assert sum(map(len, clauses)) == saved["input_literals"]
        caps = saved["caps"]
        for observation in saved["width"]["sweep"]:
            replayed = closure(nvars, clauses, observation["width"],
                               caps["max_clauses"], caps["max_steps"])
            assert observation["status"] == replayed["status"]
            assert observation["reason"] == replayed["reason"]
            assert observation["closure_size"] == replayed["closure_size"]
            assert observation["candidate_steps"] == replayed["candidate_steps"]
            if observation["status"] == "UNSAT":
                assert replayed["contains_empty"]
        minimum = saved["width"]["minimum_refutation_width"]
        assert minimum == expected_widths[saved["name"]]
        assert saved["width"]["final_stats"]["known_clauses"] == saved["width"]["sweep"][-1]["closure_size"]
        assert saved["name"] in scaling_by_name
        source_cdcl = scaling_by_name[saved["name"]]
        assert saved["cdcl"]["status"] == source_cdcl["status"] == "UNSAT"
        assert saved["cdcl"]["proof_events"] == source_cdcl["proof_events"]
        assert saved["cdcl"]["stats"] == source_cdcl["stats"]
        source_frontier = frontier_by_name[saved["name"]]
        assert saved["frontier"] == source_frontier["frontier"]["stats"]
        assert saved["frontier"]["max_width"] >= 0
    assert artifact["all_width_cases_exact"]
    expected_hashes = {
        "resolution_width_lab/resolution.py": digest(ROOT / "resolution_width_lab" / "resolution.py"),
        "proof_complexity_scaling_lab/SCALING_RESULTS.json": digest(
            ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json"
        ),
        "proof_complexity_frontier_lab/FRONTIER_RESULTS.json": digest(
            HERE / "FRONTIER_RESULTS.json"
        ),
        "proof_complexity_frontier_lab/run_width_bridge.py": digest(HERE / "run_width_bridge.py"),
        "proof_complexity_frontier_lab/review_width_bridge.py": digest(
            HERE / "review_width_bridge.py"
        ),
        "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
    }
    assert artifact["source_sha256"] == expected_hashes
    output = {
        "status": "PASS",
        "case_count": len(artifact["rows"]),
        "width_replay_matches": True,
        "cdcl_rows_match": True,
        "frontier_rows_match": True,
        "source_hashes_match": True,
    }
    (HERE / "WIDTH_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
