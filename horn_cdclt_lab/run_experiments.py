"""Generate the mixed Horn/affine gadget audit and its independent replay."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys

import engine


ROOT = Path(__file__).resolve().parent


def eval_clause(clause, bits):
    return any((lit > 0) == bool(bits[abs(lit) - 1]) for lit in clause)


def replay_horn(clauses, cert):
    i = cert["clause_index"]
    if not (0 <= i < len(clauses)):
        return False
    assignment = cert["assignment"]
    clause = clauses[i]
    unassigned = [lit for lit in clause if abs(lit) - 1 not in assignment]
    true_lits = [lit for lit in clause
                 if abs(lit) - 1 in assignment and assignment[abs(lit) - 1] == (lit > 0)]
    if true_lits:
        return False
    if cert["kind"] == "horn-prop":
        return len(unassigned) == 1 and unassigned[0] == cert["lit"]
    return cert["kind"] == "horn-conflict" and not unassigned


def replay_affine(equations, cert):
    assignment = cert["assignment"]
    combo = cert["combo"]
    mask = rhs = 0
    for i, (m, r) in enumerate(equations):
        if (combo >> i) & 1:
            mask ^= m
            rhs ^= r
    assigned_mask = sum(1 << v for v in assignment)
    assigned_bits = sum(1 << v for v, val in assignment.items() if val)
    residual_mask = mask & ~assigned_mask
    residual_rhs = rhs ^ (mask & assigned_bits).bit_count() % 2
    if cert["kind"] == "affine-conflict":
        return residual_mask == 0 and residual_rhs == 1
    return (cert["kind"] == "affine-prop" and
            residual_mask == (1 << cert["var"]) and
            residual_rhs == int(cert["value"]))


def replay_all(horn, affine, certificates):
    checks = []
    for item in certificates:
        cert = item["certificate"]
        if item["theory"] == "horn":
            checks.append(replay_horn(horn.clauses, cert))
        elif item["theory"] == "affine":
            checks.append(replay_affine(affine.equations, cert))
        else:
            checks.append(False)
    return all(checks)


def solve_and_review(clauses):
    n, horn, affine = engine.encode_exact_one(clauses)
    solver = engine.MixedPortfolioSolver(n, horn=horn, affine=affine)
    solution = solver.solve()
    return {
        "clauses": [list(c) for c in clauses],
        "direct_sat": engine.direct_exact_one_sat(clauses) is not None,
        "encoded_sat": solution is not None,
        "nodes": solver.stats["nodes"],
        "decisions": solver.stats["decisions"],
        "conflicts": solver.stats["conflicts"],
        "propagations": solver.stats["propagations"],
        "horn_props": solver.stats["horn_props"],
        "affine_props": solver.stats["affine_props"],
        "horn_conflicts": solver.stats["horn_conflicts"],
        "affine_conflicts": solver.stats["affine_conflicts"],
        "certificates": len(solver.certificates),
        "independent_certificate_replay": replay_all(horn, affine, solver.certificates),
        "solution_valid": (solution is None or all(sum(solution[v - 1] for v in c) == 1
                                                    for c in clauses)),
    }


def main():
    table = engine.gadget_projection_table()
    projection_ok = all(bool(ws) == (sum(target) == 1)
                        for target, ws in table.items())

    corpus = []
    triples4 = engine.all_triples(4)
    for r in range(len(triples4) + 1):
        for subset in itertools.combinations(triples4, r):
            corpus.append(solve_and_review(list(subset)))

    scaling = []
    for n in range(3, 11):
        row = solve_and_review(engine.all_triples(n))
        row["target_variables"] = n
        scaling.append(row)

    results = {
        "status": "executed research audit; no P=NP result",
        "gadget_projection": {"table": {"".join(map(str, k)): v for k, v in table.items()},
                              "exact_one_match": projection_ok},
        "small_corpus": {
            "formula_count": len(corpus),
            "all_sat_statuses_match": all(x["direct_sat"] == x["encoded_sat"] for x in corpus),
            "all_solutions_valid": all(x["solution_valid"] for x in corpus),
            "all_certificates_replay": all(x["independent_certificate_replay"] for x in corpus),
        },
        "complete_triple_scaling": scaling,
    }
    (ROOT / "RESULTS.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    review = {
        "independent_reviewer": "run_experiments.py replay_horn/replay_affine",
        "projection_ok": projection_ok,
        "small_corpus_ok": results["small_corpus"],
        "scaling_ok": all(x["direct_sat"] == x["encoded_sat"] and
                           x["solution_valid"] and x["independent_certificate_replay"]
                           for x in scaling),
        "all_checks_passed": projection_ok and all(results["small_corpus"].values()) and
                             all(x["direct_sat"] == x["encoded_sat"] and
                                 x["solution_valid"] and x["independent_certificate_replay"]
                                 for x in scaling),
    }
    (ROOT / "REVIEW.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": results, "review": review}, indent=2))
    return 0 if review["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
