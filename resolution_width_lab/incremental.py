"""Incremental bounded-width closure with explicit seed reuse."""
from __future__ import annotations

import hashlib
import json

from resolution import BoundedResolution, normalize_clause, resolve, weakenings


def compact(result, *, seed_clauses=0):
    clauses = sorted(result["clauses"])
    clause_digest = hashlib.sha256(
        json.dumps(clauses, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "status": result["status"],
        "reason": result.get("reason"),
        "closure_size": len(result["clauses"]),
        "candidate_steps": result["stats"]["candidate_steps"],
        "seed_clauses": seed_clauses,
        "clause_digest": clause_digest,
    }


def solve_incremental(nvars, clauses, width, previous_clauses=(), *,
                      max_clauses=10000, max_steps=100000):
    """Saturate width ``width`` after seeding a complete lower-width closure.

    The seed is valid only when it came from a completed closure at a smaller
    width. The caller records that provenance; this function never treats a
    cap-truncated result as a complete seed.
    """
    known = {tuple(clause) for clause in previous_clauses
             if len(tuple(clause)) <= width}
    queue = sorted(known)
    for raw in clauses:
        clause = normalize_clause(raw)
        if clause is None or len(clause) > width or clause in known:
            continue
        if len(known) >= max_clauses:
            return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                    "clauses": [list(item) for item in sorted(known)],
                    "stats": {"candidate_steps": 0}}
        known.add(clause)
        queue.append(clause)
    if () in known:
        return {"status": "UNSAT", "reason": None,
                "clauses": [list(item) for item in sorted(known)],
                "stats": {"candidate_steps": 0}}

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
                        "clauses": [list(item) for item in sorted(known)],
                        "stats": {"candidate_steps": steps}}
            if weakened not in known:
                if len(known) >= max_clauses:
                    return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                            "clauses": [list(item) for item in sorted(known)],
                            "stats": {"candidate_steps": steps}}
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
                            "clauses": [list(item) for item in sorted(known)],
                            "stats": {"candidate_steps": steps}}
                if result not in known:
                    if len(known) >= max_clauses:
                        return {"status": "UNKNOWN", "reason": "CLAUSE_CAP",
                                "clauses": [list(item) for item in sorted(known)],
                                "stats": {"candidate_steps": steps}}
                    known.add(result)
                    queue.append(result)
                if result == ():
                    return {"status": "UNSAT", "reason": None,
                            "clauses": [list(item) for item in sorted(known)],
                            "stats": {"candidate_steps": steps}}
    return {"status": "UNKNOWN", "reason": "NO_WIDTH_W_REFUTATION",
            "clauses": [list(item) for item in sorted(known)],
            "stats": {"candidate_steps": steps}}


def run_ladder(nvars, clauses, *, max_clauses=10000, max_steps=100000):
    """Return exact scratch-vs-incremental rows through the first refutation."""
    max_width = max((len(clause) for clause in clauses), default=0)
    previous = ()
    rows = []
    for width in range(max_width + 1):
        baseline = BoundedResolution(
            nvars, clauses, width,
            max_clauses=max_clauses, max_steps=max_steps,
        ).solve()
        incremental = solve_incremental(
            nvars, clauses, width, previous,
            max_clauses=max_clauses, max_steps=max_steps,
        )
        compact_baseline = compact(baseline)
        compact_incremental = compact(incremental, seed_clauses=len(previous))
        rows.append({"width": width, "baseline": compact_baseline,
                     "incremental": compact_incremental})
        if baseline["status"] != "UNKNOWN" and incremental["status"] != "UNKNOWN":
            assert {tuple(c) for c in baseline["clauses"]} == {
                tuple(c) for c in incremental["clauses"]
            }
        if baseline["status"] == "UNSAT" or incremental["status"] == "UNSAT":
            break
        if baseline.get("reason") in {"CLAUSE_CAP", "STEP_CAP"}:
            break
        previous = tuple(tuple(c) for c in baseline["clauses"])
    return rows
