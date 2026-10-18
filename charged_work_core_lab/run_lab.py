"""Reproduce Fano certificates and bounded coordinate-conditioning experiments.

Run from any directory. Writes results.json/results.csv beside this script. Uses
saved v17 matrices, not the old exponential all-cut auditor. No dependencies beyond
Python's standard library. Experimental solver calls have work limits; reference
enumeration and the v17 reference trellis run to completion on these small inputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "high_width_core_stress_lab"
sys.path.insert(0, str(PREVIOUS))
from core_math import rank_vectors, connectivity, graphic_cut_code_columns
from trellis_solver import enumerate_min_distance, trellis_min_nonzero_generator
from deletion_solver import (choose_deletion, conditioned_width_profile,
                             minimum_distance, parity_check)
from fano_certificate import find_fano_minor, verify_fano_certificate


def generator_from_columns(columns, k):
    return tuple(sum(1 << j for j, col in enumerate(columns) if col >> i & 1) for i in range(k))


def greedy_order(columns):
    """Same deterministic lambda-greedy order as v17, with discovery accounting."""
    started = perf_counter()
    rank = rank_vectors(columns)
    remaining = set(range(len(columns)))
    left = []
    order = []
    rank_calls = 1
    while remaining:
        scores = []
        for v in sorted(remaining):
            width = (rank_vectors(left + [columns[v]])
                     + rank_vectors([columns[j] for j in sorted(remaining) if j != v]) - rank)
            rank_calls += 2
            scores.append((width, v))
        _, v = min(scores)
        order.append(v)
        left.append(columns[v])
        remaining.remove(v)
    return {"order": order, "rank_evaluations": rank_calls, "seconds": perf_counter() - started}


def checked_solver(generator, n, expected, deleted, order, limits):
    result = minimum_distance(generator, n, deleted=deleted, order=order, **limits)
    predicted = conditioned_width_profile(generator, n, deleted, order)
    if result["status"] == "EXACT":
        if result["distance"] != expected:
            raise RuntimeError(f"distance disagreement at n={n}: {result}")
        if result["peak_syndrome_states"] != predicted["peak_syndrome_states"]:
            raise RuntimeError("measured syndrome peak disagrees with independent rank formula")
    if result["word"] is not None:
        word = result["word"]
        checks = parity_check(generator, n)
        if not word or word.bit_count() != result["upper_bound"] or any(
                (h & word).bit_count() % 2 for h in checks):
            raise RuntimeError("invalid original-code witness")
    return {"solve": result, "predicted_profile": predicted}


def run(args):
    audit_path = PREVIOUS / "random_code_audits.json"
    source_bytes = audit_path.read_bytes()
    samples = json.loads(source_bytes)
    limits = {"max_transitions": args.max_transitions, "max_branches": 4}
    output = {"schema": "non_graphic_core_experiment_v1", "python": platform.python_version(),
              "source": {"relative_path": "../high_width_core_stress_lab/random_code_audits.json",
                         "sha256": hashlib.sha256(source_bytes).hexdigest(),
                         "prior_exhaustive_scans_rerun": False},
              "limits": limits, "fano_max_trials": args.fano_trials,
              "deletion_candidate_limit": args.max_candidates,
              "interpretation": "Finite exact experiments. Fano excludes graphic/cographic matroids; "
              "it does not establish computational hardness. Conditioned width is for a fixed order.",
              "samples": [], "controls": []}
    implementation = [ROOT / name for name in ("deletion_solver.py", "fano_certificate.py", "run_lab.py")]
    implementation += [PREVIOUS / name for name in ("core_math.py", "trellis_solver.py")]
    output["implementation_sha256"] = {
        str(path.relative_to(ROOT.parent)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in implementation}
    csv_rows = []
    for sample in samples:
        n, k = sample["n"], sample["k"]
        columns = tuple(sample["columns"])
        generator = generator_from_columns(columns, k)
        if rank_vectors(columns) != k or connectivity(columns, sample["central_witness_mask"]) != sample["central_min_lambda"]:
            raise RuntimeError("prior matrix/witness consistency check failed")
        certificate_started = perf_counter()
        search = find_fano_minor(columns, max_trials=args.fano_trials, seed=8128)
        verified = None
        if search["status"] == "FOUND":
            verified = verify_fano_certificate(columns, search["certificate"])
            if not verified["valid"]:
                raise RuntimeError(f"Fano verifier rejected discovered certificate: {verified}")
        certificate_seconds = perf_counter() - certificate_started

        enum_started = perf_counter()
        distance, enum_word, visited = enumerate_min_distance(generator)
        enum_seconds = perf_counter() - enum_started
        ordering = greedy_order(columns)
        independent = trellis_min_nonzero_generator(generator, n, ordering["order"])
        if independent["distance"] != distance:
            raise RuntimeError("v17 enumeration and v17 trellis disagree")
        cases = []
        for label, order, count in [("natural", list(range(n)), 0),
                                    ("greedy", ordering["order"], 0),
                                    ("greedy_fix_1", ordering["order"], 1),
                                    ("greedy_fix_2", ordering["order"], 2)]:
            selection = choose_deletion(generator, n, count, order, args.max_candidates)
            if selection["deleted"] is None:
                cases.append({"name": label, "selection": selection, "solve": None})
                continue
            case = {"name": label, "selection": selection,
                    **checked_solver(generator, n, distance, selection["deleted"], order, limits)}
            cases.append(case)
            solve = case["solve"]
            csv_rows.append({"n": n, "dimension": k, "case": label,
                             "fano_verified": bool(verified and verified["valid"]),
                             "prior_internal4_certified": sample["mode"] == "full",
                             "prior_middle_cut_lower_bound": sample["central_min_lambda"],
                             "status": solve["status"], "distance": solve["distance"],
                             "deleted": ";".join(map(str, selection["deleted"])),
                             "peak_syndrome_states": solve["peak_syndrome_states"],
                             "peak_dp_entries": solve["peak_dp_entries"],
                             "transitions": solve["transitions"],
                             "branch_assignments": solve["branch_assignments_total"],
                             "selection_candidates": selection["candidates_evaluated"],
                             "selection_rank_evaluations": selection["rank_evaluations"],
                             "selection_seconds": selection["seconds"],
                             "solve_seconds": solve["seconds"],
                             "enumerated_codewords": visited})
        output["samples"].append({"n": n, "dimension": k, "generator_rows": list(generator),
                                   "prior_internal4_certified": sample["mode"] == "full",
                                   "prior_middle_cut_lower_bound": sample["central_min_lambda"],
                                   "fano_search": search, "fano_verification": verified,
                                   "fano_search_and_verification_seconds": certificate_seconds,
                                   "enumeration": {"distance": distance, "word": enum_word,
                                                   "codewords": visited, "seconds": enum_seconds},
                                   "order_discovery": ordering, "v17_trellis": independent,
                                   "cases": cases})
        print(f"n={n}: Fano {search['status']}; distance {distance}; "
              + ", ".join(f"{case['name']}={case['solve']['peak_syndrome_states']} states"
                          for case in cases if case.get("solve")), flush=True)

    for t in (5, 6):
        columns = graphic_cut_code_columns(t)
        search = find_fano_minor(columns, max_trials=args.fano_trials, seed=8128)
        if search["status"] == "FOUND":
            raise RuntimeError("Fano search falsely accepted a graphic control")
        output["controls"].append({"kind": "known_graphic_complete_graph", "t": t,
                                   "search": search,
                                   "interpretation": "Graphic by construction; UNKNOWN is expected search output."})
    interrupted = minimum_distance((3,), 2, max_transitions=0)
    if interrupted["status"] != "UNKNOWN" or interrupted["distance"] is not None:
        raise RuntimeError("work-limit control fabricated an exact answer")
    output["controls"].append({"kind": "zero_transition_budget", "result": interrupted})
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if csv_rows:
        with (ROOT / "results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
            writer.writeheader()
            writer.writerows(csv_rows)
    print(f"Saved {len(output['samples'])} sample audits and {len(csv_rows)} solver comparisons.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-transitions", type=int, default=1000000)
    parser.add_argument("--max-candidates", type=int, default=10000)
    parser.add_argument("--fano-trials", type=int, default=256)
    options = parser.parse_args()
    if min(options.max_transitions, options.max_candidates, options.fano_trials) < 0:
        parser.error("limits must be nonnegative")
    run(options)
