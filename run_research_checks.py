"""Run research suites in separate processes and save exact test transcripts.

This is an integration/reproduction entry point; it does not label mathematical
proofs as formally verified. Most test processes have a five-minute limit; the
full RM(2,5) independent replay has a longer limit because it rebuilds the
27,926-row quotient several times for adversarial certificate tests.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parent


def main():
    suites = [(path.stem, ROOT, ["-v", path.stem]) for path in sorted(ROOT.glob("test_*.py"))]
    suites += [("typed_merge_planner", ROOT / "typed_merge_planner_lab", ["discover", "-v"]),
              ("charged_work_core", ROOT / "charged_work_core_lab", ["discover", "-v"]),
              ("direct_fano_core", ROOT / "non_graphic_core_lab", ["discover", "-v"]),
              ("high_width_core", ROOT / "high_width_core_stress_lab", ["-v", "test_lab"]),
              ("horn_cdclt", ROOT / "horn_cdclt_lab", ["-v", "test_lab"]),
              ("proof_producing_cdcl", ROOT / "proof_producing_cdcl_lab", ["-v", "test_cdcl", "test_review_validation"]),
              ("proof_complexity_scaling", ROOT / "proof_complexity_scaling_lab", ["-v", "test_scaling"]),
              ("tseitin_expander", ROOT / "tseitin_expander_lab", ["-v", "test_tseitin"]),
              ("proof_complexity_frontier", ROOT / "proof_complexity_frontier_lab", ["-v", "test_frontier"]),
              ("resolution_width", ROOT / "resolution_width_lab", ["-v", "test_resolution"]),
              ("weighted_boundary", ROOT / "weighted_boundary_lab", ["-v", "test_lab"]),
              ("local_marginal_code", ROOT / "local_marginal_code_lab",
               ["-v", "test_local_marginal", "test_reed_muller",
                "test_all_dual_reed_muller", "test_all_dual_local_reed_muller",
                "test_reed_muller_level_d", "test_reed_muller_level_d_flat_star"]),
              ("local_marginal_hierarchy_note", ROOT / "local_marginal_code_lab",
               ["-v", "test_local_marginal_hierarchy_note",
                "test_sparse_parity_clause_comparison"]),
              ("local_marginal_affine_overlap", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_level_d_affine_overlap"]),
              ("exact_lp_discovery", ROOT / "local_marginal_code_lab",
               ["-v", "test_exact_lp_model", "test_exact_lp_verify", "test_exact_lp_soplex"]),
              ("quadratic_rm_level8", ROOT / "local_marginal_code_lab",
               ["-v", "test_rm2_level8_family"]),
              ("quadratic_rm_level9", ROOT / "local_marginal_code_lab",
               ["-v", "test_rm2_nine_scope", "test_rm2_level9_family"]),
              ("local_marginal_full_level8", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_level_d_full"]),
              ("local_marginal_sos_moment", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_moment"]),
              ("local_marginal_sos_strengthened", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_strengthened"]),
              ("local_marginal_sos_two_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_two_cut"]),
              ("local_marginal_sos_three_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_three_cut"]),
              ("local_marginal_sos_four_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_four_cut"]),
              ("local_marginal_sos_five_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_five_cut"]),
              ("local_marginal_sos_six_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_six_cut"]),
              ("local_marginal_sos_seven_cut", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_seven_cut"]),
              ("local_marginal_sos_candidate_scan", ROOT / "local_marginal_code_lab",
               ["-v", "test_reed_muller_sos_candidate_scan"]),
              ("representation_discovery", ROOT / "representation_discovery_lab",
                 ["-v", "test_engine", "test_nonlinear_control",
                  "test_baseline", "test_independent_review"]),
              ("affine_projection_recognition", ROOT / "affine_projection_recognition_lab",
                 ["-v", "test_lab", "test_quantified_boundary", "test_hull_engine", "test_hull_certificate"]),
              ("affine_character_factor", ROOT / "affine_character_factor_lab", ["discover", "-v"]),
              ("labelled_join_certified", ROOT / "labelled_join_certified", ["discover", "-v"])]
    def hashes():
        paths = sorted({p for _, directory, _ in suites for p in directory.glob("*.py")})
        return {p.relative_to(ROOT.parent).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths}
    before = hashes()
    started_utc = datetime.now(timezone.utc).isoformat()
    results = []
    transcripts = []
    for name, directory, arguments in suites:
        print(f"Running {name}...", flush=True)
        started = perf_counter()
        try:
            timeout = 900 if name == "local_marginal_full_level8" else 300
            completed = subprocess.run([sys.executable, "-m", "unittest", *arguments], cwd=directory,
                                       capture_output=True, text=True, timeout=timeout)
            output = completed.stdout + completed.stderr
            returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            output = decoded(exc.stdout) + decoded(exc.stderr) + f"\nTIMEOUT after {timeout} seconds\n"
            returncode = None
        elapsed = perf_counter() - started
        count = re.search(r"Ran (\d+) tests? in", output)
        results.append({"suite": name, "returncode": returncode,
                        "test_methods": int(count.group(1)) if count else None,
                        "seconds": elapsed, "passed": returncode == 0})
        transcripts.append(f"Suite: {name}\n{output}")
        print(f"{name}: {'PASS' if returncode == 0 else 'FAIL'} ({elapsed:.2f}s)", flush=True)
    after = hashes()
    summary = {"all_suites_passed": all(row["passed"] for row in results) and before == after,
               "source_unchanged_during_tests": before == after,
               "started_utc": started_utc, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "python": sys.version, "suites": results,
               "test_methods_total": sum(row["test_methods"] or 0 for row in results),
               "implementation_sha256": after}
    (ROOT / "TEST_OUTPUT.txt").write_text("\n".join(transcripts), encoding="utf-8")
    (ROOT / "TEST_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["all_suites_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
