"""Replay the bounded exact campaign and save inputs plus LF-normalized hashes."""

import hashlib
import io
import json
from pathlib import Path
import platform
import random
import time
import unittest

import moments
import test_global_moment


HERE = Path(__file__).resolve().parent
SOURCE_PATHS = [
    HERE / name for name in (
        "moments.py", "test_global_moment.py", "run_experiments.py", "THEOREM.md")
] + [HERE.parent / "REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md"]


def hashes():
    return {
        str(path.relative_to(HERE.parent)).replace("\\", "/"):
        hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for path in SOURCE_PATHS
    }


def run():
    started = time.perf_counter()
    before = hashes()
    output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_global_moment)
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError(output.getvalue())
    requests = [(D, m) for D in range(3, 13) for m in (D, D + 1, D + 4, D + 17)]
    requests += [(31, 64), (64, 128), (256, 512)]
    records = []
    for D, m in requests:
        data = moments.parameters(D, m)
        if data["mixed_variance"] != 0 or data["contrast"] <= 0:
            raise AssertionError("Gram data")
        if m > D and not (data["additive_gap"] > 0
                          and data["degree_four_square_value"] < 0):
            raise AssertionError("gap or next-moment negative control")
        records.append({"original_request": {"D": D, "m": m},
                        "exact_data": moments.json_value(data)})
    rng = random.Random(20261020)
    scopes = []
    for D, m in ((3, 4), (4, 5), (5, 6), (6, 7)):
        for _ in range(2):
            scope = rng.sample(range(1, 1 << m), D + 4)
            check = test_global_moment.local_review(D, m, scope)
            scopes.append({
                "original_request": {"D": D, "m": m, "scope": scope},
                "old_table": moments.json_value(moments.scope_table(D, m, scope, repaired=False)),
                "repaired_table": moments.json_value(moments.scope_table(D, m, scope)),
                "independent_check": check,
            })
    after = hashes()
    if before != after:
        raise RuntimeError("source or dependency changed during run")
    record = {
        "format": "global-moment-extension-v1",
        "status": "PASS",
        "scope": "Hybrid exact-projection L_(D+4) plus the global Boolean M_1 only",
        "not_claimed": ["hybrid optimum", "full Lasserre feasibility",
                        "formal proof verification", "novelty"],
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "elapsed_seconds": time.perf_counter() - started,
        "source_hash_convention": "SHA256 after CRLF-to-LF normalization",
        "source_sha256": after,
        "source_unchanged_during_run": True,
        "unit_tests": {"run": result.testsRun, "failures": len(result.failures),
                       "errors": len(result.errors), "skipped": len(result.skipped),
                       "transcript": output.getvalue()},
        "formula_case_count": len(records),
        "formula_cases": records,
        "saved_local_scope_count": len(scopes),
        "saved_local_atom_count": sum(item["independent_check"]["atoms"] for item in scopes),
        "local_scopes": scopes,
        "independent_test_methods": [
            "rational dense-matrix elimination",
            "entrywise rank-one plus projector Gram identity",
            "enumerated actual codimension-two subspaces",
            "full original-monomial expansion of linear and quadratic squares",
            "exact quadratic-code projection row spans and direct superset sums",
            "below-threshold and matrix-entry mutations",
        ],
    }
    (HERE / "RESULTS.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: record[key] for key in (
        "status", "elapsed_seconds", "formula_case_count",
        "saved_local_scope_count", "saved_local_atom_count")}, indent=2))
    return record


if __name__ == "__main__":
    run()
