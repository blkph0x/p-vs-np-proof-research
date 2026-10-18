"""Reproduce exact rank-compressed affine experiments with independent optima.

The supplied basis is part of each input. This runner does not discover bases,
claim general coverage, or enumerate all codewords of the larger instances.
Eight primary certificates are retained; the 72 small all-target checks retain
compact outcome records instead of duplicate certificates.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
from itertools import combinations
import json
from pathlib import Path
import platform
from time import perf_counter

from rank_native_solver import solve_rank_native, verify_rank_native


ROOT = Path(__file__).resolve().parent
LIMITS = {"max_states": 256, "max_dp_transitions": 1_000_000, "max_graph_calls": 257}
SOURCE_NAMES = ("run_rank_experiments.py", "rank_native_solver.py",
                "native_coset_solver.py", "matching_certificate.py")
ORIGINAL_RESEARCH_REQUEST = (
    "The goal is to create a P = NP solver or find a solution to this question; "
    "think outside the box, test rigorously, prove guesses before treating them "
    "as established, and avoid unsupported claims."
)
EXPERIMENT_REQUEST = (
    "Test the supplied-basis family consisting of reduced incidence of K_(3p+1) "
    "and every nonzero linear combination of p disjoint triple-supported vectors, "
    "for p=1..8. Use affine targets with repeating block weights 1,2,3 and "
    "require_nonzero=False. Compare against the independently proved closed form; "
    "exhaust all targets for p=1 and p=2. Retain all eight primary certificates, "
    "source hashes, original inputs and timings. Inspect archived six best-found "
    "transforms for exception-rank compression without fresh solves. Cap states "
    "at 256, DP transitions at 1000000, and graph calls at 257."
)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                    sort_keys=True).encode("utf-8")).hexdigest()


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_NAMES}


def rank_binary(values):
    """Independent elimination on bit-packed GF(2) vectors."""
    pivots = {}
    for value in values:
        while value:
            bit = value & -value
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


def rows_from_columns(columns, row_count):
    return [sum(1 << j for j, column in enumerate(columns) if column >> bit & 1)
            for bit in range(row_count)]


def columns_from_rows(rows, n):
    return [sum(((row >> j) & 1) << i for i, row in enumerate(rows))
            for j in range(n)]


def syndrome_from_rows(rows, word):
    return sum(((row & word).bit_count() % 2) << i for i, row in enumerate(rows))


def family(p):
    if type(p) is not int or not 1 <= p <= 8:
        raise ValueError("this bounded runner constructs only 1 <= p <= 8")
    row_count = 3 * p
    graph_columns = [(1 << u if u < row_count else 0) ^
                     (1 << v if v < row_count else 0)
                     for u, v in combinations(range(row_count + 1), 2)]
    basis = [7 << (3 * j) for j in range(p)]
    exceptional = [sum(basis[j] for j in range(p) if mask >> j & 1)
                   for mask in range(1, 1 << p)]
    columns = graph_columns + exceptional
    rows = rows_from_columns(columns, row_count)
    if (len(set(columns)) != len(columns) or
            any(column.bit_count() > 2 for column in graph_columns) or
            any(column.bit_count() <= 2 for column in exceptional) or
            rank_binary(exceptional) != p or rank_binary(rows) != row_count):
        raise ArithmeticError("family construction failed independent structural checks")
    return {"p": p, "n": len(columns), "row_count": row_count,
            "dimension": len(columns) - row_count,
            "graph_columns": len(graph_columns), "exception_columns": len(exceptional),
            "exception_basis": basis, "original_columns": columns,
            "original_check_rows": rows,
            "original_columns_sha256": digest(columns),
            "original_check_rows_sha256": digest(rows),
            "row_transform": [1 << j for j in range(row_count)]}


def target_formula(p, target):
    """Closed form proved in RANK_NATIVE_RESULTS.md; does not call the solver."""
    if type(target) is not int or not 0 <= target < 1 << (3 * p):
        raise ValueError("target outside the constructed row space")
    weights = [((target >> (3 * j)) & 7).bit_count() for j in range(p)]
    without_exception = (sum(weights) + 1) // 2
    residual = sum(min(a, 3 - a) for a in weights)
    force_nonempty = not any(a >= 2 for a in weights)
    if force_nonempty:
        residual += min(3 - 2 * a for a in weights)
    with_exception = 1 + (residual + 1) // 2
    return {"block_weights": weights, "target_weight": sum(weights),
            "zero_exception_optimum": without_exception,
            "best_nonzero_exception_residual_weight": residual,
            "nonempty_block_set_correction_used": force_nonempty,
            "nonzero_exception_optimum": with_exception,
            "optimum": min(without_exception, with_exception)}


def checked_solve(instance, target):
    request = {"n": instance["n"], "original_check_rows": instance["original_check_rows"],
               "row_transform": instance["row_transform"], "target": target,
               "require_nonzero": False, "limits": dict(LIMITS)}
    reference = target_formula(instance["p"], target)
    started = perf_counter()
    result = solve_rank_native(request["original_check_rows"], request["n"],
                               row_transform=request["row_transform"], target=target,
                               require_nonzero=False, **LIMITS)
    replay_started = perf_counter()
    replay = verify_rank_native(request["original_check_rows"], request["n"], result,
                                target=target, require_nonzero=False)
    replay_seconds = perf_counter() - replay_started
    word = result["word"]
    if (not replay["valid"] or result["status"] != "EXACT" or
            result["distance"] != reference["optimum"] or
            result["exception_rank"] != instance["p"] or
            result["state_count"] != 1 << instance["p"] or
            result["exceptional_coordinates"] !=
            list(range(instance["graph_columns"], instance["n"])) or
            len(result["branches"]) != 1 << instance["p"]):
        raise ArithmeticError("rank solver, certificate, family structure or closed form disagreed")
    if (type(word) is not int or word < 0 or word.bit_length() > instance["n"] or
            word.bit_count() != reference["optimum"] or
            syndrome_from_rows(instance["original_check_rows"], word) != target):
        raise ArithmeticError("word failed the independently checked original affine request")
    return {"original_request": request, "original_request_sha256": digest(request),
            "formula_reference": reference, "rank_native_result": result,
            "independent_replay": replay,
            "independent_replay_seconds": replay_seconds,
            "formula_agreement": True, "original_word_valid": True,
            "solve_and_two_verifications_seconds": perf_counter() - started}


def primary_case(p):
    instance = family(p)
    target = sum(((1 << (1 + j % 3)) - 1) << (3 * j) for j in range(p))
    checked = checked_solve(instance, target)
    return {"kind": "complete_graph_plus_all_nonzero_exception_syndromes",
            **instance, "target": target,
            "coordinate_assignment_count_without_syndrome_compression": 1 << instance["exception_columns"],
            "coordinate_assignments_enumerated": False,
            "basis_supplied": True, "basis_discovery_performed": False,
            "checked": checked}


def tiny_coordinate_reference(instance):
    """Exhaust ALL full words only for p=1, n=7; no large enumeration."""
    if instance["p"] != 1 or instance["n"] != 7:
        raise ValueError("full-coordinate reference is restricted to the seven-coordinate case")
    best = {}
    for word in range(1 << instance["n"]):
        target = syndrome_from_rows(instance["original_check_rows"], word)
        best[target] = min(best.get(target, instance["n"] + 1), word.bit_count())
    return best


def exception_subset_reference(instance, target):
    """Enumerate <=8 exceptional subsets, using the separate graph cost theorem."""
    if instance["p"] > 2:
        raise ValueError("subset reference is restricted to the two smallest cases")
    exceptions = instance["original_columns"][instance["graph_columns"]:]
    best = instance["n"] + 1
    for subset in range(1 << len(exceptions)):
        residual = target
        for j, column in enumerate(exceptions):
            if subset >> j & 1:
                residual ^= column
        best = min(best, subset.bit_count() + (residual.bit_count() + 1) // 2)
    return best


def all_small_targets(p):
    instance = family(p)
    started = perf_counter()
    full_reference = tiny_coordinate_reference(instance) if p == 1 else None
    outcomes = []
    for target in range(1 << (3 * p)):
        checked = checked_solve(instance, target)
        result = checked["rank_native_result"]
        expected = checked["formula_reference"]["optimum"]
        if exception_subset_reference(instance, target) != expected:
            raise ArithmeticError("exception-subset reference disagrees with formula")
        if full_reference is not None and full_reference[target] != expected:
            raise ArithmeticError("full-coordinate enumeration disagrees with formula")
        outcomes.append([target, expected, result["word"]])
    return {"p": p, "n": instance["n"], "targets_checked": len(outcomes),
            "targets": "every integer from 0 through 2^(3p)-1 inclusive",
            "require_nonzero": False, "all_exact": True, "all_replays_valid": True,
            "all_formula_agreements": True, "all_exception_subset_agreements": True,
            "full_coordinate_words_enumerated": 1 << instance["n"] if p == 1 else 0,
            "all_full_coordinate_agreements": True if p == 1 else None,
            "exception_subsets_checked": len(outcomes) * (1 << instance["exception_columns"]),
            "optimum_histogram": dict(sorted(Counter(row[1] for row in outcomes).items())),
            "compact_outcome_encoding": "Each row is [original target, exact optimum, original-coordinate word].",
            "compact_outcomes": outcomes, "compact_outcomes_sha256": digest(outcomes),
            "full_certificates_retained": False,
            "seconds": perf_counter() - started}


def archive_rank_counts():
    """Read, validate and count saved transforms; do not run any archived solve."""
    source_path = ROOT / "ROW_BASIS_RESULTS.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    records = []
    for case in source["cases"]:
        rows, transform = case["original_check_rows"], case["discovery"]["row_transform"]
        transformed = []
        for mask in transform:
            value = 0
            for j, row in enumerate(rows):
                if mask >> j & 1:
                    value ^= row
            transformed.append(value)
        if (rank_binary(transform) != len(rows) or
                any(mask.bit_length() > len(rows) for mask in transform) or
                transformed != case["discovery"]["transformed_check_rows"] or
                digest(rows) != case["original_check_rows_sha256"]):
            raise ArithmeticError("archived transformed matrix failed direct verification")
        columns = columns_from_rows(transformed, case["n"])
        indices = [j for j, column in enumerate(columns) if column.bit_count() > 2]
        exceptional = [columns[j] for j in indices]
        p, q = rank_binary(exceptional), len(exceptional)
        if indices != case["native_result"]["exceptional_coordinates"]:
            raise ArithmeticError("archived exceptions disagree with transformed matrix")
        records.append({"n": case["n"], "dimension": case["dimension"],
                        "original_check_rows_sha256": digest(rows),
                        "row_transform": transform,
                        "transformed_check_rows_sha256": digest(transformed),
                        "exceptional_coordinates": indices, "exception_columns": q,
                        "exception_rank": p, "coordinate_assignment_count": 1 << q,
                        "syndrome_state_count": 1 << p,
                        "rank_compression_improves_state_count": p < q,
                        "prior_coordinate_solver_status": case["native_result"]["status"],
                        "fresh_solver_run": False, "basis_global_optimality_claimed": False})
    return {"source_file": source_path.name,
            "source_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "cases": records, "fresh_solver_runs": 0}


def markdown_report(data):
    lines = [
        "# Rank-compressed native affine experiments",
        "",
        "This is a deterministic exact experiment on a supplied-basis family. "
        "It establishes agreement with an independent closed-form optimum for these "
        "instances. It does not settle P versus NP, establish a general polynomial "
        "algorithm, or establish a new complexity theorem.",
        "",
        "## Construction and original request",
        "",
        "For each p from 1 through 8, take r=3p non-ground vertices and one ground "
        "vertex. The graph columns are the reduced incidence columns of the complete "
        "graph K_(3p+1). For j=0,...,p-1 let g_j have ones exactly at row positions "
        "3j, 3j+1, 3j+2. Append every nonzero combination of the g_j, in increasing "
        "combination-bitmask order. These q=2^p-1 columns are distinct and each has "
        "weight at least three; their binary rank is p. The graph columns have "
        "weight one or two, and the supplied row transform is the identity.",
        "",
        "The exact problem is min |x| subject to Hx=s over GF(2), with "
        "`require_nonzero=False`. Primary targets have block weights 1,2,3,1,2,3,...; "
        "in each block the first a_j row bits are one. The JSON preserves H in both "
        "row and column form, each target, each identity transform, the original "
        "solver request and its hash. Its `research_request_summary` records the "
        "larger research objective; `experiment_request` records this bounded test.",
        "",
        "## Independent closed-form proof",
        "",
        "First consider only the complete graph. If a reduced syndrome has w one "
        "bits, each selected edge can account for at most two of them, so at least "
        "ceil(w/2) edges are necessary. Pair the marked vertices by graph edges; "
        "when w is odd, join the remaining vertex to ground. This attains "
        "ceil(w/2), proving the exact graph cost for every syndrome.",
        "",
        "Write a_j in {0,1,2,3} for the target weight in block j. A zero exceptional "
        "syndrome is cheapest with no exceptional coordinates, and has total "
        "cost C0=ceil((sum_j a_j)/2). Every nonzero exceptional syndrome is itself "
        "one appended column, so its minimum exceptional cost is exactly one. "
        "Using any larger subset with that same syndrome cannot improve the "
        "graph part or its total cost. Selecting block j in that syndrome replaces "
        "a_j by 3-a_j in the residual graph target.",
        "",
        "Without the requirement to select a nonempty set of blocks, the minimum "
        "residual weight is R0=sum_j min(a_j,3-a_j). If any a_j is at least two, "
        "this minimum already selects a nonempty block set. Otherwise every a_j "
        "is zero or one, every toggle strictly raises the residual weight, and "
        "the cheapest nonempty set is a single block with smallest increase "
        "min_j(3-2a_j). Thus set R=R0 in the first case and "
        "R=R0+min_j(3-2a_j) in the second. Since ceil(w/2) is nondecreasing, the "
        "best cost with nonzero exceptional syndrome is C1=1+ceil(R/2). The exact "
        "affine optimum is min(C0,C1). This proof applies to all targets and every "
        "positive p, including the zero target where C0=0.",
        "",
        "## Primary results",
        "",
        "Every row below completed with status EXACT, passed the independent "
        "certificate replay, matched the formula, and had its returned word "
        "checked directly against the original affine equations. The JSON "
        "retains all eight full certificates, including all DP layers, final "
        "exceptional witnesses and graph optimality evidence.",
        "",
        "| p | n | Graph columns | Exceptional columns q | Rank states | Graph calls | DP transitions | Affine optimum | Produce (s) | Replay (s) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in data["primary_cases"]:
        result = case["checked"]["rank_native_result"]
        lines.append(f"| {case['p']} | {case['n']} | {case['graph_columns']} | "
                     f"{case['exception_columns']} | {result['state_count']} | "
                     f"{len(result['branches'])} | {result['dp_transitions']} | "
                     f"{result['distance']} | {result['solve_seconds']:.6f} | "
                     f"{case['checked']['independent_replay_seconds']:.6f} |")
    lines.extend([
        "",
        "`Produce` is the solver's reported construction time before its own "
        "verification. `Replay` is the runner's additional certificate check. "
        "The JSON also records the solver's own verification time and total time "
        "for construction plus both checks. Timings are single measurements in "
        "the local environment and are not comparative benchmarks; other work "
        "may have been running. Timing is never used to establish correctness.",
        "",
        "At p=8 there are 555 coordinates, including 255 distinct exceptional "
        "columns of rank eight. The solver covers all 256 syndrome cases. A "
        "coordinate-assignment enumeration would contain 2^255 assignments; "
        "that count is a combinatorial comparison, not an executed baseline or "
        "a measured speedup. The experiment's state, transition and graph-call "
        "caps are respectively 256, 1,000,000 and 257. For this explicit family "
        "q=2^p-1, so the general O(q 2^p) DP bound is polynomial in the explicit "
        "family input size. This property does not hold for arbitrary matrices.",
        "",
        "## Small exhaustive controls",
        "",
        "The runner solves all 8 targets for p=1 and all 64 targets for p=2, "
        "including zero, with the same affine semantics and budgets. Each "
        "certificate is replayed and each answer compared to the closed form. "
        "It additionally enumerates every exceptional-coordinate subset (two "
        "and eight subsets per target respectively), using the independently "
        "proved complete-graph cost. For p=1 it independently enumerates all "
        "128 full coordinate words once and compares the minimum for each "
        "target. No full-coordinate enumeration is used for p=2 or larger.",
        "",
        "| p | Targets | All checks agree | Full words enumerated | Exceptional subsets checked | Seconds |",
        "|---:|---:|:---:|---:|---:|---:|",
    ])
    for small in data["small_all_target_checks"]:
        lines.append(f"| {small['p']} | {small['targets_checked']} | Yes | "
                     f"{small['full_coordinate_words_enumerated']} | "
                     f"{small['exception_subsets_checked']} | {small['seconds']:.6f} |")
    lines.extend([
        "",
        "For these 72 checks the JSON stores compact target/optimum/word outcomes "
        "and their hash, rather than duplicating all certificates. The runner "
        "reconstructs and checks them on rerun.",
        "",
        "## Archived best-found transforms: counts only",
        "",
        "The six previously saved row transforms were read from "
        "`ROW_BASIS_RESULTS.json`, their row operations checked directly, and "
        "the exceptional-column ranks recomputed. No new optimization or "
        "archived solve was run, and no global optimality of these transforms "
        "is asserted.",
        "",
        "| n | Exceptional columns q | Exception rank p | Coordinate assignments | Syndrome states | State-count improvement |",
        "|---:|---:|---:|---:|---:|:---:|",
    ])
    for case in data["archived_transform_rank_counts"]["cases"]:
        lines.append(f"| {case['n']} | {case['exception_columns']} | {case['exception_rank']} | "
                     f"{case['coordinate_assignment_count']} | {case['syndrome_state_count']} | "
                     f"{'Yes' if case['rank_compression_improves_state_count'] else 'No'} |")
    lines.extend([
        "",
        "These archived transforms all have p=q, so rank compression does not "
        "reduce their state counts. In particular, this method has not closed "
        "the previously recorded gaps on the larger archived cases.",
        "",
        "## Reproduction and limits",
        "",
        "Run `python run_rank_experiments.py` from this directory to reproduce "
        "both result files. Source files are hashed before and after the "
        "experiments; the runner refuses to publish if a source changes during "
        "the run. `RANK_NATIVE_RESULTS.json` records these SHA256 hashes, its "
        "Python and NetworkX versions, the archived-input hash, per-case inputs "
        "and certificates. Matrix and request hashes use compact UTF-8 JSON; "
        "dictionary keys are sorted. File hashes use their exact stored bytes.",
        "",
        f"Recorded environment: Python {data['environment']['python']}, "
        f"NetworkX {data['environment']['networkx']}. "
        f"Run started at {data['started_utc']}; total measured experiment time "
        f"before output serialization was {data['experiment_seconds']:.6f} seconds.",
        "",
        "The certified class consists of graph coordinates and disjoint "
        "exceptional coordinates in a supplied row basis. It is not an arbitrary "
        "low-rank perturbation on the same graph coordinates. The exactness "
        "claim relies on complete syndrome DP and complete graph-case coverage; "
        "arbitrary rank p still produces exponentially many states. These "
        "examples supply the basis directly and provide no general basis-finding "
        "algorithm. The analytic optimum and successful finite checks validate "
        "this implementation route; they do not prove unrestricted tractability "
        "or either answer to P versus NP.",
        "",
    ])
    return "\n".join(lines)


def main():
    started = perf_counter()
    before = source_hashes()
    data = {"schema": "rank_native_affine_experiments_v1",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "research_request_summary": ORIGINAL_RESEARCH_REQUEST,
            "experiment_request": EXPERIMENT_REQUEST,
            "environment": {"python": platform.python_version(),
                            "networkx": version("networkx"), "platform": platform.platform()},
            "limits": dict(LIMITS),
            "supplied_basis_only": True, "general_coverage_claimed": False,
            "p_vs_np_resolved": False, "novelty_claimed": False,
            "primary_cases": [], "small_all_target_checks": []}
    for p in range(1, 9):
        case = primary_case(p)
        data["primary_cases"].append(case)
        result = case["checked"]["rank_native_result"]
        print(f"Primary p={p}, n={case['n']}, q={case['exception_columns']}: "
              f"{result['status']}, optimum={result['distance']}, "
              f"{len(result['branches'])} syndrome cases, formula and replay passed", flush=True)
    for p in (1, 2):
        small = all_small_targets(p)
        data["small_all_target_checks"].append(small)
        print(f"Small p={p}: all {small['targets_checked']} targets passed", flush=True)
    data["archived_transform_rank_counts"] = archive_rank_counts()
    after = source_hashes()
    if before != after:
        raise RuntimeError("source changed during experiment; rerun before publishing results")
    data["source_sha256"] = after
    data["sources_unchanged_during_run"] = True
    data["experiment_seconds"] = perf_counter() - started
    # Certificates are kept as JSON integer data; no floating-point proof step is used.
    result_path = ROOT / "RANK_NATIVE_RESULTS.json"
    result_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (ROOT / "RANK_NATIVE_RESULTS.md").write_text(markdown_report(data), encoding="utf-8")
    print(f"Saved {result_path.name} ({result_path.stat().st_size} bytes) and RANK_NATIVE_RESULTS.md", flush=True)


if __name__ == "__main__":
    main()
