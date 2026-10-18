"""Run research suites in separate processes and save exact test transcripts.

This is an integration/reproduction entry point; it does not label mathematical
proofs as formally verified. Individual test processes have a five-minute limit.
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
              ("proof_producing_cdcl", ROOT / "proof_producing_cdcl_lab", ["-v", "test_cdcl"]),
              ("proof_complexity_scaling", ROOT / "proof_complexity_scaling_lab", ["-v", "test_scaling"]),
              ("resolution_width", ROOT / "resolution_width_lab", ["-v", "test_resolution"]),
              ("weighted_boundary", ROOT / "weighted_boundary_lab", ["-v", "test_lab"]),
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
            completed = subprocess.run([sys.executable, "-m", "unittest", *arguments], cwd=directory,
                                       capture_output=True, text=True, timeout=300)
            output = completed.stdout + completed.stderr
            returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            output = decoded(exc.stdout) + decoded(exc.stderr) + "\nTIMEOUT after 300 seconds\n"
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
