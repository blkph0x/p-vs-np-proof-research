"""Independent replay of the semantic-clutter width control."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
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
    # Width one has only the original unit clauses for these controls. Keep the
    # general finite enumerator here so the reviewer checks the saved contract.
    present = {abs(literal) for literal in clause}
    missing = [variable for variable in range(1, nvars + 1) if variable not in present]
    from itertools import product
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


def clutter_formula(clique_variables):
    z = clique_variables + 1
    clauses = [(z,), (-z,)]
    clauses += [(left + 1, right + 1)
                for left, right in combinations(range(clique_variables), 2)]
    return clique_variables + 1, tuple(clauses)


def adjacency(nvars, clauses):
    output = [0] * nvars
    for clause in clauses:
        variables = sorted({abs(literal) - 1 for literal in clause})
        for left_index, left in enumerate(variables):
            for right in variables[left_index + 1:]:
                output[left] |= 1 << right
                output[right] |= 1 << left
    return output


def boundary(mask, graph):
    result = 0
    remaining = mask
    while remaining:
        bit = remaining & -remaining
        variable = bit.bit_length() - 1
        remaining ^= bit
        if graph[variable] & ~mask:
            result |= bit
    return result.bit_count()


def optimal_order(nvars, clauses):
    graph = adjacency(nvars, clauses)
    limit = 1 << nvars
    values = [nvars + 1] * limit
    chosen = [0] * limit
    values[0] = 0
    cut_values = [0] * limit
    for mask in range(1, limit):
        cut_values[mask] = boundary(mask, graph)
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            candidate = max(values[mask ^ bit], cut_values[mask])
            if candidate < values[mask]:
                values[mask] = candidate
                chosen[mask] = bit
    mask = limit - 1
    reverse_order = []
    while mask:
        bit = chosen[mask]
        assert bit
        reverse_order.append(bit.bit_length() - 1)
        mask ^= bit
    order = reverse_order[::-1]
    prefix = 0
    widths = []
    for variable in order:
        prefix |= 1 << variable
        widths.append(cut_values[prefix])
    return values[-1], order, widths


def row_width(nvars, clauses, order):
    graph = adjacency(nvars, clauses)
    prefix = 0
    widths = []
    for variable in order:
        prefix |= 1 << variable
        widths.append(boundary(prefix, graph))
    return widths


def has_model(nvars, clauses, *, omit_literal):
    # The remaining positive clique clauses accept the all-true clique point;
    # set z to satisfy whichever single unit remains.
    reduced = [clause for clause in clauses if clause != omit_literal]
    assignment = [True] * nvars
    for clause in reduced:
        if len(clause) == 1:
            assignment[abs(clause[0]) - 1] = clause[0] > 0
    return all(any(assignment[abs(literal) - 1] == (literal > 0)
                   for literal in clause) for clause in reduced)


def main():
    artifact = json.loads((HERE / "CLUTTER_RESULTS.json").read_text(encoding="utf-8"))
    for saved in artifact["rows"]:
        nvars, clauses = clutter_formula(saved["clique_size"])
        assert nvars == saved["nvars"]
        assert [list(clause) for clause in clauses] == saved["clauses"]
        assert len(clauses) == saved["clause_count"]
        assert sum(map(len, clauses)) == saved["input_literals"]
        caps = saved["caps"]
        zero = closure(nvars, clauses, 0, caps["max_clauses"], caps["max_steps"])
        one = closure(nvars, clauses, 1, caps["max_clauses"], caps["max_steps"])
        for actual, expected in ((zero, saved["resolution_width_zero"]),
                                 (one, saved["resolution_width_one"])):
            assert actual["status"] == expected["status"]
            assert actual["reason"] == expected["reason"]
            assert actual["closure_size"] == expected["closure_size"]
            assert actual["candidate_steps"] == expected["candidate_steps"]
        assert zero["status"] == "UNKNOWN" and not zero["contains_empty"]
        assert one["status"] == "UNSAT" and one["contains_empty"]
        assert saved["resolution_width_one"]["known_clauses"] == 3
        row_order = [saved["clique_size"]] + list(range(saved["clique_size"]))
        assert row_order == saved["row_order"]
        widths = row_width(nvars, clauses, row_order)
        assert widths == saved["row_prefix_widths"]
        assert max(widths, default=0) == saved["row_width"]
        minimum, order, optimal_widths = optimal_order(nvars, clauses)
        assert order == saved["optimal_order"]
        assert optimal_widths == saved["optimal_prefix_widths"]
        assert minimum == saved["optimal_width"] == max(0, saved["clique_size"] - 1)
        assert saved["row_width"] == minimum
        assert has_model(nvars, clauses, omit_literal=(saved["clique_size"] + 1,))
        assert has_model(nvars, clauses, omit_literal=(-(saved["clique_size"] + 1),))
    assert artifact["all_rows_exact"]
    expected_hashes = {
        "resolution_width_lab/resolution.py": digest(ROOT / "resolution_width_lab" / "resolution.py"),
        "proof_complexity_frontier_lab/order_dp.py": digest(HERE / "order_dp.py"),
        "proof_complexity_frontier_lab/run_clutter.py": digest(HERE / "run_clutter.py"),
        "proof_complexity_frontier_lab/review_clutter.py": digest(HERE / "review_clutter.py"),
        "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
    }
    assert artifact["source_sha256"] == expected_hashes
    output = {"status": "PASS", "case_count": len(artifact["rows"]),
              "width_replay_matches": True, "frontier_replay_matches": True,
              "unit_mutations_have_models": True, "source_hashes_match": True}
    (HERE / "CLUTTER_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
