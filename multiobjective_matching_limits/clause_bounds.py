"""SAT-to-simultaneously-bounded perfect matching, with explicit tiny oracles.

The reduction is polynomial; the enumeration helpers are deliberately bounded
experiments, not a polynomial SAT or constrained-matching solver.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import random
from time import perf_counter


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def normalize_cnf(variable_count, clauses):
    """Remove repeated literals and tautologies; retain empty clauses."""
    _integer(variable_count, "variable_count")
    if type(clauses) not in (list, tuple):
        raise ValueError("clauses must be a list or tuple")
    normalized, origins, tautologies = [], [], []
    for index, clause in enumerate(clauses):
        if type(clause) not in (list, tuple):
            raise ValueError("each clause must be a list or tuple")
        if any(type(lit) is not int or lit == 0 or abs(lit) > variable_count for lit in clause):
            raise ValueError("literal must be a signed, nonzero variable index")
        unique = set(clause)
        if any(-lit in unique for lit in unique):
            tautologies.append(index)
            continue
        normalized.append(sorted(unique, key=lambda lit: (abs(lit), lit)))
        origins.append(index)
    return {"clauses": normalized, "original_indices": origins,
            "dropped_tautologies": tautologies}


def build_instance(variable_count, clauses):
    """Each C4's matchings {0,2} and {1,3} encode false and true."""
    norm = normalize_cnf(variable_count, clauses)
    cycle_count = max(variable_count, int(any(not clause for clause in norm["clauses"])))
    edges = []
    for i in range(cycle_count):
        a = 4 * i
        edges.extend([[a, a + 1], [a + 1, a + 2], [a + 2, a + 3], [a, a + 3]])
    costs, bounds = [], []
    for clause in norm["clauses"]:
        row = [0] * len(edges)
        if not clause:
            # Every perfect matching of the first C4 selects two cost-one edges.
            row[:4] = [1] * 4
            bound = 1
        else:
            for literal in clause:
                row[4 * (abs(literal) - 1) + int(literal < 0)] = 1
            bound = len(clause) - 1
        costs.append(row)
        bounds.append(bound)
    request = {"variable_count": variable_count, "clauses": [list(c) for c in clauses]}
    return {"format": "clause-bounded-C4-matching-v1", "request": request,
            "request_sha256": sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "normalization": norm, "cycle_count": cycle_count, "vertex_count": 4 * cycle_count,
            "edges": edges, "costs": costs, "bounds": bounds}


def verify_bounded_matching(vertex_count, edges, costs, bounds, matching):
    """Check original graph coverage and every original linear bound exactly."""
    try:
        _integer(vertex_count, "vertex_count")
        for value, name in ((edges, "edges"), (costs, "costs"), (bounds, "bounds"), (matching, "matching")):
            if type(value) not in (list, tuple):
                raise ValueError(f"{name} must be a list or tuple")
        for edge in edges:
            if type(edge) not in (list, tuple) or len(edge) != 2:
                raise ValueError("malformed edge")
            u, v = edge
            if type(u) is not int or type(v) is not int or not 0 <= u < v < vertex_count:
                raise ValueError("invalid edge endpoints")
        if len(costs) != len(bounds):
            raise ValueError("cost/bound dimension mismatch")
        for row, bound in zip(costs, bounds):
            _integer(bound, "bound")
            if type(row) not in (list, tuple) or len(row) != len(edges):
                raise ValueError("cost row dimension mismatch")
            for weight in row:
                _integer(weight, "edge cost")
        covered = set()
        for edge_id in matching:
            if type(edge_id) is not int or not 0 <= edge_id < len(edges):
                raise ValueError("invalid selected edge ID")
            u, v = edges[edge_id]
            if u in covered or v in covered:
                raise ValueError("repeated vertex in matching")
            covered.update((u, v))
        if len(covered) != vertex_count:
            raise ValueError("matching does not cover every vertex")
        values = [sum(row[j] for j in matching) for row in costs]
        violations = [j for j, (value, bound) in enumerate(zip(values, bounds)) if value > bound]
        return {"valid": not violations, "perfect_matching": True, "costs": values,
                "violated_bounds": violations, "errors": []}
    except (ValueError, TypeError, IndexError) as exc:
        return {"valid": False, "perfect_matching": False, "costs": None,
                "violated_bounds": None, "errors": [str(exc)]}


def check_instance_matching(instance, matching):
    return verify_bounded_matching(instance["vertex_count"], instance["edges"],
                                   instance["costs"], instance["bounds"], matching)


def assignment_matching(instance, assignment, *, dummy_value=0):
    n = instance["request"]["variable_count"]
    _integer(assignment, "assignment")
    if assignment.bit_length() > n:
        raise ValueError("assignment exceeds original variable count")
    if type(dummy_value) is not int or dummy_value not in (0, 1):
        raise ValueError("dummy_value must be 0 or 1")
    matching = []
    for i in range(instance["cycle_count"]):
        value = (assignment >> i) & 1 if i < n else dummy_value
        matching.extend((4 * i + value, 4 * i + value + 2))
    return matching


def cnf_value(variable_count, clauses, assignment):
    normalize_cnf(variable_count, clauses)  # Validation only; evaluate original clauses.
    _integer(assignment, "assignment")
    if assignment.bit_length() > variable_count:
        raise ValueError("assignment exceeds variable count")
    return all(any(bool((assignment >> (abs(lit) - 1)) & 1) == (lit > 0)
                   for lit in clause) for clause in clauses)


def oracle_perfect_matchings(vertex_count, edges, *, max_vertices=24, max_matchings=4096):
    """Independent generic graph recursion; it does not know the C4 encoding."""
    _integer(max_vertices, "max_vertices")
    _integer(max_matchings, "max_matchings")
    if type(vertex_count) is not int or vertex_count < 0 or vertex_count > max_vertices:
        raise ValueError("graph enumeration vertex budget exceeded")
    found = []

    def visit(remaining, chosen):
        if not remaining:
            if len(found) >= max_matchings:
                raise ValueError("graph enumeration matching budget exceeded")
            found.append(tuple(chosen))
            return
        vertex = min(remaining)
        for j, (u, v) in enumerate(edges):
            other = v if u == vertex else (u if v == vertex else None)
            if other is not None and other in remaining:
                visit(remaining - {vertex, other}, chosen + [j])

    visit(set(range(vertex_count)), [])
    return found


def audit_formula(variable_count, clauses, *, max_assignments=4096):
    """Compare all original truth assignments with all generic graph matchings."""
    _integer(max_assignments, "max_assignments", 1)
    normalize_cnf(variable_count, clauses)
    if variable_count >= max_assignments.bit_length():
        raise ValueError("truth-table enumeration budget exceeded")
    instance = build_instance(variable_count, clauses)
    truth = {assignment for assignment in range(1 << variable_count)
             if cnf_value(variable_count, clauses, assignment)}
    matchings = oracle_perfect_matchings(instance["vertex_count"], instance["edges"],
                                        max_matchings=max(2, max_assignments))
    accepted, checked_costs = set(), 0
    for matching in matchings:
        selected = set(matching)
        assignment = sum(int(4 * i + 1 in selected) << i for i in range(variable_count))
        for i in range(instance["cycle_count"]):
            local = selected & set(range(4 * i, 4 * i + 4))
            if local not in ({4 * i, 4 * i + 2}, {4 * i + 1, 4 * i + 3}):
                raise ArithmeticError("generic oracle found a third cycle matching")
        result = check_instance_matching(instance, list(matching))
        if not result["perfect_matching"]:
            raise ArithmeticError("generic graph witness failed exact coverage")
        for clause, cost in zip(instance["normalization"]["clauses"], result["costs"]):
            expected = (2 if not clause else sum(bool((assignment >> (abs(lit) - 1)) & 1) != (lit > 0)
                                                for lit in clause))
            if cost != expected:
                raise ArithmeticError("clause objective is not its false-literal count")
            checked_costs += 1
        if result["valid"]:
            accepted.add(assignment)
    if accepted != truth:
        raise ArithmeticError("bounded matching and original SAT disagree")
    return {"instance": instance, "satisfying_assignments": sorted(truth),
            "accepted_assignments": sorted(accepted), "assignments_checked": 1 << variable_count,
            "matchings_checked": len(matchings), "clause_costs_checked": checked_costs}


def _source_hashes(directory):
    names = ("clause_bounds.py", "test_clause_bounds.py", "THEOREM.md")
    return {name: sha256((directory / name).read_bytes()).hexdigest() for name in names}


def run_experiments():
    directory = Path(__file__).resolve().parent
    sources, started = _source_hashes(directory), perf_counter()
    totals = {"formulas_checked": 0, "assignments_checked": 0, "matchings_checked": 0,
              "clause_costs_checked": 0}

    def accumulate(n, clauses):
        audit = audit_formula(n, clauses)
        totals["formulas_checked"] += 1
        for key in totals:
            if key != "formulas_checked":
                totals[key] += audit[key]
        return audit

    for n in range(4):
        pool = [[]]
        for size in range(1, min(n, 3) + 1):
            for variables in combinations(range(1, n + 1), size):
                pool.extend([list(clause) for clause in product(*[(v, -v) for v in variables])])
        for count in range(min(2, len(pool)) + 1):
            for indices in combinations(range(len(pool)), count):
                accumulate(n, [pool[index] for index in indices])
    exhaustive_count = totals["formulas_checked"]
    rng = random.Random(20261018)
    for _ in range(300):
        n = rng.randrange(6)
        clauses = [[rng.choice((-1, 1)) * rng.randint(1, n) for _ in range(rng.randrange(6))]
                   if n else [] for _ in range(rng.randrange(9))]
        accumulate(n, clauses)
    named = {
        "SAT_three_clauses": (3, [[1, 2, 3], [-1, 2], [-2, 3]]),
        "UNSAT_opposite_units": (1, [[1], [-1]]),
        "UNSAT_all_eight_ternary_clauses": (3, [list(c) for c in product((1, -1), (2, -2), (3, -3))]),
        "normalization": (2, [[1, 1, 1], [1, -1, 2], [-2, -2]]),
        "empty_formula": (0, []),
        "empty_clause": (0, [[]]),
    }
    controls = []
    for name, (n, clauses) in named.items():
        audit = accumulate(n, clauses)
        instance = audit["instance"]
        witnesses = []
        for assignment in range(1 << n):
            matching = assignment_matching(instance, assignment)
            witnesses.append({"assignment": assignment, "matching": matching,
                              "verification": check_instance_matching(instance, matching)})
        controls.append({"name": name, **audit, "witnesses": witnesses})
    if _source_hashes(directory) != sources:
        raise RuntimeError("source changed during experiment")
    result = {"schema": "multiobjective_C4_SAT_reduction_v1", "source_sha256": sources,
              "source_unchanged_during_run": True, "seed": 20261018,
              "summary": {**totals, "exhaustive_formulas": exhaustive_count, "seeded_formulas": 300,
                          "named_controls": len(controls), "general_matching_optimizer_used": False},
              "controls": controls, "elapsed_seconds": perf_counter() - started}
    (directory / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run_experiments()["summary"]))
