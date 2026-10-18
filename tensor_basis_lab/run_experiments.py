"""Preserve original formulas, rational bases, transformed entries and traces."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from time import perf_counter

import tensor_basis as tb
from test_tensor_basis import BASES, direct_original_count


def _hashes(directory):
    return {name: sha256((directory / name).read_bytes()).hexdigest() for name in (
        "tensor_basis.py", "test_tensor_basis.py", "run_experiments.py", "THEOREM.md")}


def run():
    directory = Path(__file__).resolve().parent
    before, started = _hashes(directory), perf_counter()
    cases, locals_only, wrong_controls = [], [], []
    summary = {"requests": 0, "exact_contractions": 0, "unknown_contractions": 0,
               "verified_contraction_certificates": 0, "original_assignments_enumerated": 0,
               "local_transform_certificates": 0, "wrong_same_basis_controls": 0,
               "exact_cases_with_negative_transformed_terms": 0}

    def request(n, clauses, basis_name, mode):
        return {"n": n, "clauses": clauses, "basis_name": basis_name,
                "basis": [[tb.encode_rational(v) for v in row] for row in BASES[basis_name]], "mode": mode}

    def add(name, n, clauses, basis_name, mode):
        original = request(n, clauses, basis_name, mode)
        start = perf_counter()
        result = tb.solve_basis(n, clauses, original["basis"], mode=mode)
        solve_seconds = perf_counter() - start
        verification, reference = None, None
        verify_seconds = 0
        signs = None
        if result["status"] == "EXACT":
            check_start = perf_counter()
            verification = tb.verify_basis(n, clauses, original["basis"], result["certificate"], mode=mode)
            verify_seconds = perf_counter() - check_start
            if not verification["valid"] or verification["count"] != result["count"]:
                raise AssertionError("original-input contraction proof did not verify")
            if n <= 8:
                count = direct_original_count(n, clauses, mode)
                reference = {"method": "bounded original logical assignments and explicit local slack choices",
                             "count": count, "logical_assignments": 1 << n}
                summary["original_assignments_enumerated"] += 1 << n
                if result["count"] != [count, 1]:
                    raise AssertionError("basis result disagrees with direct original count")
            elif not clauses:
                reference = {"method": "proved factor two for each unused variable", "count": 1 << n,
                             "logical_assignments": 0}
                if result["count"] != [1 << n, 1]:
                    raise AssertionError("unused-variable multiplicity was lost")
            values = [tb.decode_rational(v) for v in result["certificate"]["transformed_terms"]]
            signs = {"positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values),
                     "zero": sum(v == 0 for v in values)}
            summary["exact_cases_with_negative_transformed_terms"] += int(signs["negative"] > 0)
            summary["exact_contractions"] += 1
            summary["verified_contraction_certificates"] += 1
        else:
            if result["status"] != "UNKNOWN" or result["count"] is not None or result["certificate"] is not None:
                raise AssertionError("unfinished contraction made a final count claim")
            summary["unknown_contractions"] += 1
        cases.append({"name": name, "request": original, "result": result,
                      "independent_verification": verification, "original_count_reference": reference,
                      "transformed_term_signs": signs,
                      "solve_seconds": solve_seconds, "verify_seconds": verify_seconds})
        summary["requests"] += 1

    examples = [
        ("empty_product", 0, []), ("empty_clause", 0, [[]]),
        ("unused_variables", 4, [[1]]), ("contradictory_units", 1, [[1], [-1]]),
        ("shared_mixed_polarity", 3, [[1, -2], [2, 3], [-1, -3]]),
        ("repeated_ternary_clause", 3, [[1, 2, 3], [1, 2, 3]]),
        ("repeated_occurrence", 2, [[1, 1, 1], [-1, 2]]),
        ("one_positive_ternary", 3, [[1, 2, 3]]),
    ]
    for name, n, clauses in examples:
        for basis_name in ("identity", "Hadamard", "rational"):
            for mode in ("sat", "slack"):
                add(f"{name}/{basis_name}/{mode}", n, clauses, basis_name, mode)
    for signs in product((-1, 1), repeat=3):
        clause = [[sign * (i + 1) for i, sign in enumerate(signs)]]
        for mode in ("sat", "slack"):
            add("ternary_polarity_" + "".join("p" if sign > 0 else "n" for sign in signs) + "/" + mode,
                3, clause, "shear", mode)
    for mode in ("sat", "slack"):
        add("signed_diagonal/" + mode, 2, [[1, -2]], "signed", mode)
        add("nonorthogonal_integer/" + mode, 2, [[1, 2], [-1, 2]], "nonorthogonal", mode)
        add("local_degree_limit/" + mode, 1, [[1]] * 30, "Hadamard", mode)
        clauses = [[i, i + 1] for i in range(1, 20)]
        add("global_contraction_limit/" + mode, 20, clauses, "Hadamard", mode)
        original = request(20, clauses, "Hadamard", mode)
        local = tb.transform_network(20, clauses, original["basis"], mode=mode, max_edge_assignments=0)
        check = tb.verify_transformation(20, clauses, original["basis"], local["certificate"], mode=mode, max_edge_assignments=0)
        if local["status"] != "EXACT" or not check["valid"]:
            raise AssertionError("local transformation should not enumerate global edge assignments")
        locals_only.append({"request": original, "result": local, "verification": check,
                            "scope": "Local basis transformation only; no global count is claimed."})
        summary["local_transform_certificates"] += 1
    add("256_unused_variables", 256, [], "Hadamard", "sat")
    for name, expected in (("Hadamard", 2), ("shear", 3)):
        original = request(1, [[1]], name, "sat")
        bad = tb.wrong_same_basis_control(1, [[1]], original["basis"])
        if bad["original_count"] != [1, 1] or bad["wrong_count"] != [expected, 1]:
            raise AssertionError("same-basis countercontrol disagrees with the direct unit-clause calculation")
        wrong_controls.append({"request": original, "control": bad})
        summary["wrong_same_basis_controls"] += 1
    if before != _hashes(directory):
        raise RuntimeError("source changed during experiment")
    result = {"schema": "rational_tensor_basis_controls_v1", "scope": "Exact rational basis invariance and bounded reference contractions; no tractable-family recognition or general polynomial evaluator.",
              "indexing": "edge IDs by clause/literal occurrence; local port0 is the least significant bit",
              "limits": tb.DEFAULT_LIMITS, "summary": summary, "cases": cases,
              "local_transform_controls": locals_only, "wrong_same_basis_controls": wrong_controls,
              "source_sha256": before, "source_unchanged_during_run": True,
              "elapsed_seconds": perf_counter() - started}
    (directory / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run()["summary"]))
