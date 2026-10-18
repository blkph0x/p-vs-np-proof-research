"""Bounded, reproducible graph-lift experiments against original code problems.

Every certificate is replayed against the original matrix, target and weights.
Small instances use exhaustive full-word references. Larger complete-graph
instances use an elementary weight-three certificate, when one exists, and the
independent labelled-join checker. No universal representation is claimed.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform
import random
from time import perf_counter

from code_lift_solver import solve_code, verify_code
from sparse_lift_normal_form import (
    build_sparse_lift_normal_form, verify_sparse_lift_normal_form,
)


ROOT = Path(__file__).resolve().parent
SEED = 2026101807
SOURCES = ("labelled_tables.py", "labelled_tjoin.py", "code_lift_solver.py",
           "sparse_lift_normal_form.py", "run_lift_experiments.py")
LIMITS = {"max_states": 4096, "max_total_states": 1_000_000,
          "max_relaxations": 1_000_000, "max_dp_states": 65536,
          "max_dp_transitions": 1_000_000, "max_verification_arcs": 10_000_000}
VERIFY_LIMITS = {"verification_state_limit": 1_000_000,
                 "verification_arc_limit": 10_000_000,
                 "verification_dp_transitions": 1_000_000}
MAX_PIN_CASES = 64
MAX_OUTPUT_BYTES = 30_000_000


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                    sort_keys=True).encode("utf-8")).hexdigest()


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCES}


def rows_from_columns(columns, r):
    return [sum(1 << j for j, value in enumerate(columns) if value >> i & 1)
            for i in range(r)]


def columns_from_rows(rows, n):
    return [sum(((row >> j) & 1) << i for i, row in enumerate(rows)) for j in range(n)]


def syndrome(rows, word):
    return sum(((row & word).bit_count() % 2) << i for i, row in enumerate(rows))


def cost(weights, word):
    return sum(w for j, w in enumerate(weights) if word >> j & 1)


def transform_rows(rows, transform):
    output = []
    for combination in transform:
        value = 0
        for i, row in enumerate(rows):
            if combination >> i & 1:
                value ^= row
        output.append(value)
    return output


def inverse_binary(rows):
    size = len(rows)
    left, right = list(rows), [1 << j for j in range(size)]
    for j in range(size):
        pivot = next((i for i in range(j, size) if left[i] >> j & 1), None)
        if pivot is None:
            raise ArithmeticError("generated row transformation is singular")
        left[j], left[pivot] = left[pivot], left[j]
        right[j], right[pivot] = right[pivot], right[j]
        for i in range(size):
            if i != j and left[i] >> j & 1:
                left[i] ^= left[j]
                right[i] ^= right[j]
    return right


def scrambled_rows(rows, rng):
    r = len(rows)
    scramble = [1 << j for j in range(r)]
    if r >= 2:
        for _ in range(3 * r):
            i, j = rng.sample(range(r), 2)
            scramble[i] ^= scramble[j]
    original = transform_rows(rows, scramble)
    restore = inverse_binary(scramble)
    if transform_rows(original, restore) != rows:
        raise ArithmeticError("original-row scrambling failed round trip")
    return original, restore


def exhaustive_reference(rows, n, target, require_nonzero, weights):
    if not 0 <= n <= 15:
        raise ValueError("full-word enumeration is explicitly restricted to n<=15")
    started = perf_counter()
    best, feasible = None, 0
    for word in range(1 << n):
        if (require_nonzero and not word) or syndrome(rows, word) != target:
            continue
        feasible += 1
        candidate = cost(weights, word), word
        if best is None or candidate < best:
            best = candidate
    return {"kind": "EXHAUSTIVE_ORIGINAL_COORDINATE_WORDS", "certified_optimum": True,
            "optimum": best[0] if best is not None else None,
            "word": best[1] if best is not None else None,
            "words_visited": 1 << n, "feasible_words": feasible,
            "seconds": perf_counter() - started}


def graph_triangle_reference(columns, edges):
    """Independent d>=3 from distinct nonzero columns, d<=3 from a triangle."""
    if any(not column for column in columns) or len(set(columns)) != len(columns):
        raise ArithmeticError("simple complete-graph columns must be distinct and nonzero")
    index = {edge: j for j, edge in enumerate(edges)}
    vertices = 1 + max(max(edge) for edge in edges)
    checked = 0
    for a, b, c in combinations(range(vertices), 3):
        checked += 1
        positions = [index[a, b], index[a, c], index[b, c]]
        if columns[positions[0]] ^ columns[positions[1]] ^ columns[positions[2]] == 0:
            return {"kind": "DISTINCT_NONZERO_COLUMNS_AND_ZERO_LABEL_TRIANGLE",
                    "certified_optimum": True, "optimum": 3,
                    "word": sum(1 << j for j in positions), "triangle_vertices": [a, b, c],
                    "lower_bound": 3, "triangles_checked": checked, "words_visited": 0}
    return {"kind": "DISTINCT_NONZERO_COLUMN_LOWER_BOUND_ONLY",
            "certified_optimum": False, "optimum": None, "lower_bound": 3,
            "triangles_checked": checked, "words_visited": 0}


def join_certificates(native):
    if native["schema"] == "certified_labelled_tjoin_v1":
        return [native]
    if native["mode"] == "DIRECT":
        return [native["direct"]]
    return [case["residual"] for case in native["cases"]]


def case_record(name, kind, rows, n, graph_rows, *, target=0, require_nonzero=True,
                weights=None, row_transform=None, reference=None, extra=None):
    rows = list(rows)
    weights = [1] * n if weights is None else list(weights)
    transform = [1 << j for j in range(len(rows))] if row_transform is None else list(row_transform)
    request = {"check_rows": rows, "n": n, "graph_rows": graph_rows,
               "row_transform": transform, "target": target,
               "require_nonzero": require_nonzero, "weights": weights,
               "limits": dict(LIMITS), "max_pin_cases": MAX_PIN_CASES}
    if reference is None:
        reference = exhaustive_reference(rows, n, target, require_nonzero, weights)
    started = perf_counter()
    result = solve_code(**request)
    solve_wall = perf_counter() - started
    verify_started = perf_counter()
    checked = verify_code(rows, n, result, target=target, require_nonzero=require_nonzero,
                          weights=weights, **VERIFY_LIMITS)
    verification_seconds = perf_counter() - verify_started
    if result["status"] != "EXACT" or not checked["valid"] or checked["status"] != "EXACT":
        raise ArithmeticError(f"{name}: exact certificate was not accepted: {checked}")
    if reference["certified_optimum"] and result["distance"] != reference["optimum"]:
        raise ArithmeticError(f"{name}: independently computed optimum disagreed")
    word = result["word"]
    if word is not None:
        if (type(word) is not int or word < 0 or word.bit_length() > n or
                (require_nonzero and not word) or syndrome(rows, word) != target or
                cost(weights, word) != result["distance"]):
            raise ArithmeticError(f"{name}: returned word failed original request")
    elif reference["certified_optimum"] and reference["optimum"] is not None:
        raise ArithmeticError(f"{name}: a known feasible request was called infeasible")
    joins = join_certificates(result["native"])
    return {"name": name, "kind": kind, "original_request": request,
            "original_request_sha256": digest(request), "original_check_rows_sha256": digest(rows),
            "original_columns": columns_from_rows(rows, n),
            "reference": reference, "reference_agreement": True if reference["certified_optimum"] else None,
            "result": result, "independent_replay": checked,
            "original_word_valid": True if word is not None else None,
            "solve_wall_seconds": solve_wall, "independent_replay_seconds": verification_seconds,
            "work_summary": {"join_cases": len(joins),
                             "dp_transitions": sum(c["dp_transitions"] for c in joins),
                             "max_terminals_in_join_case": max((len(c["terminals"]) for c in joins), default=0),
                             "label_rows": len(rows) - graph_rows},
            "supplied_basis": True, "basis_discovery_performed": False,
            **(extra or {})}


def named_primary_cases():
    cases = []
    for name, columns, graph_rows in (
            ("thirteen_point_one_row_lift", [v for v in range(1, 16) if v not in (7, 15)], 3),
            ("PG_3_2_two_row_lift", list(range(1, 16)), 2)):
        rows = rows_from_columns(columns, 4)
        case = case_record(name, "named_row_form", rows, len(columns), graph_rows)
        if case["result"]["distance"] != 3:
            raise ArithmeticError("named projective controls must have minimum nonzero weight three")
        case["coverage_note"] = (
            "The 13-point representation is a one-row lift outside native rank one; see COVERAGE_AUDIT.md."
            if len(columns) == 13 else
            "This is a supplied two-row lift. The separate rank-one exclusion proof is not an automatic recognizer.")
        cases.append(case)
        print(f"Primary {name}: n={len(columns)}, optimum=3, exhaustive reference and replay passed", flush=True)
    return cases


def seeded_row_cases():
    rng = random.Random(SEED)
    cases = []
    for index in range(30):
        n, g, p = 4 + index % 9, 1 + index % 4, index % 4
        choices = [value for value in range(1 << g) if value.bit_count() <= 2]
        columns = [rng.choice(choices) | (rng.randrange(1 << p) << g) for _ in range(n)]
        row_form = rows_from_columns(columns, g + p)
        original, restore = scrambled_rows(row_form, rng)
        target = (0 if index % 5 == 0 else
                  syndrome(original, rng.randrange(1 << n)) if index % 2 == 0 else
                  rng.randrange(1 << (g + p)))
        weights = [1] * n if index % 2 == 0 else [rng.randrange(6) for _ in range(n)]
        require_nonzero = bool((index // 2) % 2)
        cases.append(case_record(f"seeded_row_form_{index:02d}", "seeded_small_row_form",
                                 original, n, g, row_transform=restore, target=target,
                                 require_nonzero=require_nonzero, weights=weights,
                                 extra={"seed": SEED, "index": index,
                                        "supplied_row_form": row_form,
                                        "weight_kind": "unit" if index % 2 == 0 else "nonnegative_integer"}))
    print("Seeded row forms: all 30 original-coordinate exhaustive references and replays passed", flush=True)
    return cases


def complete_graph_cases():
    rng = random.Random(SEED + 1)
    cases = []
    for t, p in [(t, p) for t in (4, 6, 8) for p in (1, 2)] + [(10, 2)]:
        edges = list(combinations(range(t), 2))
        graph_columns = [(1 << u if u < t - 1 else 0) ^
                         (1 << v if v < t - 1 else 0) for u, v in edges]
        labels = [rng.randrange(1 << p) for _ in edges]
        columns = [column | (label << (t - 1)) for column, label in zip(graph_columns, labels)]
        rows = rows_from_columns(columns, t - 1 + p)
        n = len(columns)
        reference = (exhaustive_reference(rows, n, 0, True, [1] * n) if n <= 6
                     else graph_triangle_reference(columns, edges))
        case = case_record(f"complete_graph_K{t}_labels{p}", "seeded_complete_graph_labels",
                           rows, n, t - 1, reference=reference,
                           extra={"seed": SEED + 1, "graph_vertices": t,
                                  "graph_edges": [list(e) for e in edges], "edge_labels": labels,
                                  "full_word_enumeration_performed": n <= 6})
        if not reference["certified_optimum"]:
            raise ArithmeticError("bounded complete-graph family lacked its independent triangle optimum")
        cases.append(case)
        print(f"Complete K{t}, p={p}, n={n}: optimum={case['result']['distance']}, "
              f"{case['work_summary']['join_cases']} pins, independent reference and replay passed", flush=True)
    return cases


def sparse_normalization_cases():
    rng = random.Random(SEED + 2)
    cases = []
    for index in range(10):
        r, n, p = 4 + index % 3, 4 + index % 9, 1 + index % 3
        choices = [value for value in range(1 << r) if value.bit_count() <= 2]
        B_columns = [rng.choice(choices) for _ in range(n)]
        B = rows_from_columns(B_columns, r)
        # Even cases create a non-ground component requiring a component-sum row;
        # odd cases connect selected vertices to ground. Both have dependent U columns.
        forest = ([(1 << j) ^ (1 << (j + 1)) for j in range(p)] if index % 2 == 0
                  else [1 << j for j in range(p)])
        U = forest + [0, forest[0]]
        if p >= 2:
            U.append(forest[0] ^ forest[1])
        V = [rng.randrange(1 << n) for _ in U]
        H = [row ^ 0 for row in B]
        for i in range(r):
            for u, value in zip(U, V):
                if u >> i & 1:
                    H[i] ^= value
        target = (0 if index % 3 == 0 else syndrome(H, rng.randrange(1 << n))
                  if index % 2 == 0 else rng.randrange(1 << r))
        normalized = build_sparse_lift_normal_form(B, U, V, n, target=target, max_work=1_000_000)
        if normalized["status"] != "EXACT":
            raise ArithmeticError("small normalizer hit a work limit")
        certificate = normalized["certificate"]
        verification = verify_sparse_lift_normal_form(B, U, V, n, certificate,
                                                     target=target, verification_work_limit=1_000_000)
        if (not verification["valid"] or certificate["H_rows"] != H or
                certificate["label_rows"] != p):
            raise ArithmeticError("normalizer disagreed with independent product or rank construction")
        weights = [1] * n if index % 2 == 0 else [rng.randrange(6) for _ in range(n)]
        case = case_record(f"sparse_U_normalized_{index:02d}", "sparse_U_normalized",
                           H, n, certificate["graph_rows"], target=target,
                           require_nonzero=bool(index % 2), weights=weights,
                           row_transform=certificate["row_transform"],
                           extra={"seed": SEED + 2, "index": index,
                                  "supplied_factorization": {"B_rows": B, "U_columns": U, "V_rows": V},
                                  "normalization_result": normalized,
                                  "normalization_independent_replay": verification})
        cases.append(case)
    print("Sparse-U normalization: all 10 original-coordinate exhaustive references and both replays passed", flush=True)
    return cases


def replay_saved_cases(cases):
    started = perf_counter()
    for case in cases:
        request, result = case["original_request"], case["result"]
        if digest(request) != case["original_request_sha256"]:
            raise ArithmeticError("serialized original request hash disagrees")
        checked = verify_code(request["check_rows"], request["n"], result,
                              target=request["target"], require_nonzero=request["require_nonzero"],
                              weights=request["weights"], **VERIFY_LIMITS)
        if not checked["valid"] or checked["status"] != "EXACT":
            raise ArithmeticError("serialized code certificate rejected")
        if case["kind"] == "sparse_U_normalized":
            factor = case["supplied_factorization"]
            checked = verify_sparse_lift_normal_form(**factor, n=request["n"],
                       certificate=case["normalization_result"]["certificate"],
                       target=request["target"], verification_work_limit=1_000_000)
            if not checked["valid"]:
                raise ArithmeticError("serialized normal-form certificate rejected")
    return {"cases_replayed": len(cases), "all_valid": True,
            "normal_forms_replayed": sum(c["kind"] == "sparse_U_normalized" for c in cases),
            "seconds": perf_counter() - started}


def markdown_report(data):
    cases = data["cases"]
    primaries = [c for c in cases if c["kind"] in ("named_row_form", "seeded_complete_graph_labels")]
    lines = ["# Certified graph-lift experiments", "",
             "All 49 requests completed EXACT, passed independent certificate replay against "
             "their original matrices and objectives, and agreed with an independent optimum. "
             "The examples use supplied graph-plus-label representations. They do not "
             "establish universal coverage, a new complexity theorem, or P=NP.", "",
             "## Primary and larger supplied representations", "",
             "The first two cases are the 13-column one-row lift and the 15-column projective "
             "matrix PG(3,2), represented with two label rows. Every original word was "
             "enumerated for these cases (8,192 and 32,768 words). The separate proof that "
             "PG(3,2) has no one-row lift is in COVERAGE_AUDIT.md; these experiments do not "
             "implement or claim an automatic representation recognizer.", "",
             "Complete-graph cases use one or two seeded random label bits on each distinct "
             "graph edge, unit weights, target zero and a nonzero-word requirement. K4 cases "
             "enumerate all 64 original words. For the larger cases, distinct nonzero check "
             "columns rule out weights one and two, and an explicit zero-label triangle "
             "proves an upper bound of three. These two facts give an independent exact "
             "optimum without enumerating all codewords. The JSON preserves each triangle.", "",
             "| Case | Coordinates | Graph rows | Label rows | Optimum | Join cases | Solve wall (s) | Replay (s) |",
             "|:---|---:|---:|---:|---:|---:|---:|---:|"]
    for case in primaries:
        req, work = case["original_request"], case["work_summary"]
        lines.append(f"| {case['name']} | {req['n']} | {req['graph_rows']} | "
                     f"{work['label_rows']} | {case['result']['distance']} | {work['join_cases']} | "
                     f"{case['solve_wall_seconds']:.6f} | {case['independent_replay_seconds']:.6f} |")
    lines.extend(["", "The largest case has 45 coordinates (K10) and two label rows. "
                  "Its 45 edge-pinned residual cases all have zero or two terminals. "
                  "No 2^45 full-word enumeration was performed. The solver's certificate "
                  "proves every pin optimum; the triangle argument independently proves "
                  "the aggregate minimum of three.", "",
                  "## Exhaustive original-coordinate controls", "",
                  "Thirty seeded small cases have 4–12 coordinates, 1–4 graph rows and "
                  "0–3 label rows. The original rows are scrambled by a generated invertible "
                  "matrix, and the inverse is supplied to the solver. Targets include zero, "
                  "targets known to be feasible, and arbitrary row syndromes. The nonzero "
                  "condition is varied. Half use unit weights and half use independently "
                  "generated integer weights from zero through five. Every one of the 2^n "
                  "original words is checked by an independent exhaustive oracle.", "",
                  "Ten further cases start from supplied sparse-U products H=B+UV. They "
                  "include zero and dependent U columns, components containing ground, "
                  "and components requiring sums of multiple original rows. The normalizer "
                  "and its independent verifier run first. The code solver then receives "
                  "the original H, original target and the certified row transform. Each "
                  "answer is compared with exhaustive enumeration on the original coordinates.", "",
                  "| Group | Cases | Infeasible requests | Zero-cost optima | Original words enumerated |",
                  "|:---|---:|---:|---:|---:|"])
    for kind in ("named_row_form", "seeded_small_row_form", "sparse_U_normalized", "seeded_complete_graph_labels"):
        group = [c for c in cases if c["kind"] == kind]
        lines.append(f"| {kind} | {len(group)} | "
                     f"{sum(c['result']['distance'] is None for c in group)} | "
                     f"{sum(c['result']['distance'] == 0 for c in group)} | "
                     f"{sum(c['reference']['words_visited'] for c in group)} |")
    lines.extend(["", "An EXACT result with a null optimum means that the specified request "
                  "is infeasible; it is not an unknown answer. Zero-weight nonempty answers "
                  "are legitimate when zero-cost coordinates are present. The original "
                  "nonzero requirement is verified independently of objective value.", "",
                  "## Evidence, limits and reproduction", "",
                  "Run `python run_lift_experiments.py` in this directory. `RESULTS.json` "
                  "stores the original request, its compact-JSON SHA256 hash, original "
                  "columns, supplied row transformation, full solver certificate, independent "
                  "replay result, reference optimum and timings for every case. The ten "
                  "normalization cases also store B,U,V and the full normalization evidence. "
                  "Certificates are serialized and parsed back before another complete replay; "
                  "all 49 code certificates and ten normalization certificates passed.", "",
                  "The four production modules and this runner are hashed before and after "
                  "the experiment. Publication fails if a source changed during the run. "
                  "Hashes of Python files use exact bytes; request hashes use sorted-key, "
                  "compact UTF-8 JSON. The result JSON is compact to avoid duplicating "
                  "formatting space around nested certificate arrays.", "",
                  "Caps per residual solve: 4,096 product states; 1,000,000 total table "
                  "states; 1,000,000 search relaxations; 65,536 terminal-DP states; "
                  "1,000,000 DP transitions; and 10,000,000 verification arcs. The nonempty "
                  "adapter permits at most 64 pinned cases. Normalization and its verifier "
                  "each have a separate 1,000,000-work-unit cap. Every experiment completed "
                  "within these caps. Work budgets are not wall-time limits.", "",
                  f"Seed: {data['seed']}. Python: {data['python']}. "
                  f"Start: {data['started_utc']}. Experiment time before final output "
                  f"serialization: {data['experiment_seconds']:.6f} seconds. "
                  "Each timing is a single local measurement with possible concurrent work. "
                  "Solve-wall measurements include the producer's internal checks; replay "
                  "is an additional independent verification. These are not comparative "
                  "benchmarks and imply no measured speedup over enumeration.", "",
                  "## Scope", "",
                  "Homogeneous nonzero optimization on a supplied p-row graphic lift has "
                  "the deterministic 2^{O(p)} polynomial-size graph algorithm proved in "
                  "COVERAGE_AUDIT.md. Arbitrary affine targets may have many graph terminals; "
                  "the implemented general-terminal subset DP is exponential in that count. "
                  "The small affine tests validate behavior, not unrestricted polynomial "
                  "running time. The normalizer converts a supplied sparse perturbation; "
                  "it does not find such a representation for an arbitrary matrix. The "
                  "coverage obstructions and missing general reduction remain unchanged.", ""])
    return "\n".join(lines)


def main():
    started = perf_counter()
    before = source_hashes()
    data = {"schema": "certified_graph_lift_experiments_v1",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "platform": platform.platform(), "seed": SEED,
            "research_goal": "Investigate P versus NP rigorously; prove claims and avoid unsupported generalization.",
            "experiment_request": "Validate supplied row forms, 30 small affine/weighted controls, "
                                  "complete-graph label families and 10 sparse-U conversions against original problems.",
            "limits": dict(LIMITS), "verification_limits": dict(VERIFY_LIMITS),
            "max_pin_cases": MAX_PIN_CASES, "output_byte_cap": MAX_OUTPUT_BYTES,
            "universal_coverage_claimed": False, "novelty_claimed": False, "p_vs_np_resolved": False}
    cases = named_primary_cases()
    cases.extend(seeded_row_cases())
    cases.extend(complete_graph_cases())
    cases.extend(sparse_normalization_cases())
    if len(cases) != 49:
        raise ArithmeticError("bounded experiment count changed unexpectedly")
    data["cases"] = cases
    data["serialized_certificate_replay"] = replay_saved_cases(json.loads(json.dumps(cases)))
    after = source_hashes()
    if before != after:
        raise RuntimeError("source changed during experiment; rerun after source freeze")
    data["source_sha256"] = after
    data["sources_unchanged_during_run"] = True
    data["summary"] = {"cases": len(cases), "all_exact": True,
                       "all_independent_replays_valid": True, "all_reference_optima_agree": True,
                       "infeasible_cases": sum(c["result"]["distance"] is None for c in cases),
                       "zero_cost_optima": sum(c["result"]["distance"] == 0 for c in cases),
                       "full_words_enumerated": sum(c["reference"]["words_visited"] for c in cases),
                       "case_kinds": dict(Counter(c["kind"] for c in cases))}
    data["experiment_seconds"] = perf_counter() - started
    encoded = json.dumps(data, separators=(",", ":")) + "\n"
    byte_count = len(encoded.encode("utf-8"))
    if byte_count > MAX_OUTPUT_BYTES:
        raise RuntimeError("full-certificate result exceeds the explicit output-byte cap")
    (ROOT / "RESULTS.json").write_text(encoded, encoding="utf-8")
    (ROOT / "RESULTS.md").write_text(markdown_report(data), encoding="utf-8")
    print(f"All {len(cases)} cases and serialized certificates passed; "
          f"saved RESULTS.json ({byte_count} bytes) and RESULTS.md", flush=True)


if __name__ == "__main__":
    main()
