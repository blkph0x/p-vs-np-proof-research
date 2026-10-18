"""Compare DFS and clause-learning search on independent exact-one controls."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys
import time

import engine
from cdcl import solve_encoded
from review_cdcl import replay_solver


ROOT = Path(__file__).resolve().parent


def coloring_formula(n, edges):
    """Positive 1-in-3 formula for 3-coloring of a graph.

    Each vertex has one color.  For an edge and color, (u_c,v_c,z) is satisfiable
    exactly when the two endpoint color literals are not both true; z is a fresh
    witness variable.  Thus the formula is satisfiable iff the graph is 3-colorable.
    """
    color = {(u, c): 1 + 3 * u + c for u in range(n) for c in range(3)}
    next_var = 3 * n + 1
    clauses = [tuple(color[u, c] for c in range(3)) for u in range(n)]
    for u, v in edges:
        for c in range(3):
            clauses.append((color[u, c], color[v, c], next_var))
            next_var += 1
    return clauses


def three_colorable(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    colors = [-1] * n

    def search(done):
        if done == n:
            return True
        uncolored = [u for u in range(n) if colors[u] < 0]
        u = max(uncolored, key=lambda x: sum(colors[y] >= 0 for y in adj[x]))
        used = {colors[y] for y in adj[u]}
        for c in range(3):
            if c in used:
                continue
            colors[u] = c
            if search(done + 1):
                return True
        colors[u] = -1
        return False

    return search(0)


def proof_metrics(solver):
    theory_widths = [len(e["clause"]) for e in solver.proof if e.get("kind") == "theory"]
    learned_widths = [len(e["clause"]) for e in solver.proof if e.get("kind") == "learned"]
    return {
        "max_theory_lemma_width": max(theory_widths, default=0),
        "max_learned_clause_width": max(learned_widths, default=0),
        "total_proof_literals": sum(len(e.get("clause", ())) for e in solver.proof
                                     if e.get("kind") in {"theory", "learned"}),
    }


FIXTURES = {
    "K4": {
        "n": 4,
        "edges": [(u, v) for u in range(4) for v in range(u + 1, 4)],
    },
    "sparse_12": {
        "n": 12,
        "edges": [(0, 5), (0, 6), (1, 3), (2, 9), (3, 6), (3, 7),
                  (3, 8), (3, 10), (3, 11), (4, 7), (4, 11), (6, 7),
                  (6, 8), (6, 10), (7, 8), (7, 9), (7, 10), (7, 11),
                  (9, 11), (10, 11)],
    },
    "sparse_14": {
        "n": 14,
        "edges": [(0, 2), (0, 4), (0, 6), (0, 11), (0, 13), (1, 3),
                  (1, 12), (1, 13), (2, 5), (2, 7), (2, 10), (3, 5),
                  (3, 6), (3, 10), (4, 5), (5, 8), (5, 9), (5, 12),
                  (7, 10), (7, 11), (7, 12), (8, 9), (8, 13), (9, 12),
                  (10, 12), (11, 12), (11, 13)],
    },
}


def one_case(name, n, edges):
    clauses = coloring_formula(n, edges)
    encoded_n, horn, affine = engine.encode_exact_one(clauses)
    dfs = engine.MixedPortfolioSolver(encoded_n, horn=horn, affine=affine)
    started = time.perf_counter()
    dfs_result = dfs.solve()
    dfs_seconds = time.perf_counter() - started
    cdcl, cdcl_result = solve_encoded(clauses)
    replay = replay_solver(cdcl)
    metrics = proof_metrics(cdcl)
    return {
        "name": name,
        "vertices": n,
        "edges": [list(e) for e in edges],
        "positive_one_in_three_clauses": len(clauses),
        "encoded_variables": encoded_n,
        "independent_three_colorable": three_colorable(n, edges),
        "dfs_sat": dfs_result is not None,
        "cdcl_sat": cdcl_result is not None,
        "dfs_nodes": dfs.stats["nodes"],
        "dfs_decisions": dfs.stats["decisions"],
        "dfs_conflicts": dfs.stats["conflicts"],
        "dfs_certificates": dfs.stats["certificates_verified"],
        "dfs_seconds": dfs_seconds,
        "cdcl_decisions": cdcl.stats["decisions"],
        "cdcl_conflicts": cdcl.stats["conflicts"],
        "cdcl_learned_clauses": cdcl.stats["learned_clauses"],
        "cdcl_resolution_steps": cdcl.stats["resolution_steps"],
        "cdcl_theory_lemmas": cdcl.stats["theory_lemmas"],
        "cdcl_proof_events": len(cdcl.proof),
        **metrics,
        "cdcl_replay": replay,
    }


def main():
    fixture_rows = [one_case(name, **fixture) for name, fixture in FIXTURES.items()]
    complete_rows = []
    for n in range(3, 11):
        clauses = engine.all_triples(n)
        cdcl, result = solve_encoded(clauses)
        metrics = proof_metrics(cdcl)
        complete_rows.append({
            "target_variables": n,
            "clauses": len(clauses),
            "sat": result is not None,
            "decisions": cdcl.stats["decisions"],
            "conflicts": cdcl.stats["conflicts"],
            "learned_clauses": cdcl.stats["learned_clauses"],
            "resolution_steps": cdcl.stats["resolution_steps"],
            **metrics,
            "replay": replay_solver(cdcl),
        })

    small = []
    triples4 = engine.all_triples(4)
    for r in range(len(triples4) + 1):
        for subset in itertools.combinations(triples4, r):
            direct = engine.direct_exact_one_sat(list(subset)) is not None
            cdcl, result = solve_encoded(list(subset))
            small.append({
                "clauses": [list(c) for c in subset],
                "direct_sat": direct,
                "cdcl_sat": result is not None,
                "replay": replay_solver(cdcl),
            })

    result = {
        "status": "clause-learning audit; no P=NP result",
        "fixtures": fixture_rows,
        "complete_triple_scaling": complete_rows,
        "small_corpus": small,
    }
    (ROOT / "CDCL_RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    review = {
        "fixtures_all_three_color_controls_unsat": all(not x["independent_three_colorable"]
                                                       for x in fixture_rows),
        "fixtures_status_match": all(x["dfs_sat"] == x["cdcl_sat"] ==
                                      x["independent_three_colorable"]
                                      for x in fixture_rows),
        "fixtures_all_proofs_replay": all(x["cdcl_replay"]["all_events_valid"] and
                                           x["cdcl_replay"]["database_size_matches"]
                                           for x in fixture_rows),
        "small_status_match": all(x["direct_sat"] == x["cdcl_sat"] for x in small),
        "small_proofs_replay": all(x["replay"]["all_events_valid"] and
                                    x["replay"]["database_size_matches"] for x in small),
        "complete_proofs_replay": all(x["replay"]["all_events_valid"] and
                                       x["replay"]["database_size_matches"]
                                       for x in complete_rows),
    }
    review["all_checks_passed"] = all(review.values())
    (ROOT / "CDCL_REVIEW.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"review": review, "fixture_summary": [
        {k: row[k] for k in ("name", "vertices", "dfs_nodes", "cdcl_decisions",
                             "cdcl_conflicts", "cdcl_learned_clauses", "cdcl_resolution_steps")}
        for row in fixture_rows]}, indent=2))
    return 0 if review["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
