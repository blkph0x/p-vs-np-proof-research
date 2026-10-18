"""Independent replay for the compact frontier/CDCL comparison."""
from __future__ import annotations

import hashlib
import json
from itertools import product, combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


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


def clause_value(clause, assignment):
    return any(bool(assignment[abs(lit) - 1]) == (lit > 0) for lit in clause)


def independent_frontier(nvars, clauses, order):
    position = {variable: index for index, variable in enumerate(order)}
    scopes = [{abs(lit) - 1 for lit in clause} for clause in clauses]
    boundaries = []
    for cut in range(nvars + 1):
        boundaries.append(tuple(variable for variable in order[:cut]
                                if any(variable in scope and
                                       any(position[other] >= cut for other in scope)
                                       for scope in scopes)))
    last = [max(position[v] for v in scope) + 1 for scope in scopes]
    states = [[0]]
    transitions = []
    total_states = 1
    total_transitions = 0
    for cut in range(1, nvars + 1):
        previous = boundaries[cut - 1]
        current = boundaries[cut]
        variable = order[cut - 1]
        completed = [index for index, end in enumerate(last) if end == cut]
        next_states = {}
        step = []
        for old_index, old_state in enumerate(states[-1]):
            assignment = {v: (old_state >> i) & 1 for i, v in enumerate(previous)}
            for bit in (0, 1):
                candidate = dict(assignment)
                candidate[variable] = bit
                if any(not clause_value(clauses[index], candidate) for index in completed):
                    continue
                state = sum((candidate[v] & 1) << i for i, v in enumerate(current))
                if state not in next_states:
                    next_states[state] = len(next_states)
                step.append((old_index, bit, next_states[state]))
        states.append([state for state, _ in sorted(next_states.items(), key=lambda item: item[1])])
        transitions.append(step)
        total_states += len(states[-1])
        total_transitions += len(step)
    return {
        "status": "EXACT",
        "reason": None,
        "sat": bool(states[-1]),
        "order": order,
        "boundaries": [list(boundary) for boundary in boundaries],
        "boundary_widths": [len(boundary) for boundary in boundaries],
        "layer_state_counts": [len(layer) for layer in states],
        "layer_transition_counts": [len(step) for step in transitions],
        "stats": {"max_width": max(map(len, boundaries), default=0),
                  "states": total_states, "transitions": total_transitions},
    }


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def expected_case(saved):
    if saved["family"] == "all_assignments":
        return saved["nvars"], all_assignment_clauses(saved["parameter"])
    return pigeonhole(saved["pigeons"], saved["holes"])


def main():
    artifact = json.loads((HERE / "FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
    scaling = json.loads((ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json").read_text(encoding="utf-8"))
    scaling_by_name = {row["name"]: row for row in scaling["rows"]}
    for saved in artifact["rows"]:
        nvars, clauses = expected_case(saved)
        assert nvars == saved["nvars"]
        assert len(clauses) == saved["clause_count"]
        assert sum(map(len, clauses)) == saved["input_literals"]
        replayed = independent_frontier(nvars, clauses, list(range(nvars)))
        assert replayed == saved["frontier"]
        source = scaling_by_name[saved["name"]]
        assert saved["cdcl"]["status"] == source["status"] == "UNSAT"
        assert saved["cdcl"]["proof_events"] == source["proof_events"]
        assert saved["cdcl"]["stats"] == source["stats"]
        assert source["name"] == saved["name"]
        if saved["family"] == "all_assignments":
            n = saved["parameter"]
            assert saved["frontier"]["stats"] == {
                "max_width": max(0, n - 1),
                "states": 2 ** n - 1,
                "transitions": 2 ** n - 2,
            }
        else:
            h = saved["parameter"]
            assert saved["frontier"]["stats"]["max_width"] == h * h
            assert saved["pigeons"] == h + 1
    assert artifact["all_frontier_cases_exact"]
    expected_hashes = {
        "proof_complexity_scaling_lab/SCALING_RESULTS.json": digest(ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json"),
        "variable_boundary_sat_lab/boundary_dp.py": digest(ROOT / "variable_boundary_sat_lab" / "boundary_dp.py"),
        "proof_complexity_frontier_lab/run_frontier.py": digest(HERE / "run_frontier.py"),
        "proof_complexity_frontier_lab/review_frontier.py": digest(HERE / "review_frontier.py"),
        "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
    }
    assert artifact["source_sha256"] == expected_hashes
    output = {"status": "PASS", "case_count": len(artifact["rows"]),
              "frontier_replay_matches": True, "cdcl_rows_match": True,
              "closed_forms_match": True, "source_hashes_match": True}
    (HERE / "FRONTIER_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
