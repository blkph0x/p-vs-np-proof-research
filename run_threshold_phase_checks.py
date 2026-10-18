"""Frozen-source tests for the threshold-composition phase only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LABS = ("threshold_composition_lab", "saturated_clause_limits",
        "multiobjective_matching_limits", "packed_cost_exact_matching")


def hashes():
    paths = [Path(__file__).resolve()]
    for lab in LABS:
        paths.extend(sorted((HERE/lab).glob("*.py")))
    return {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    before, started, start = hashes(), datetime.now(timezone.utc).isoformat(), time.perf_counter()
    results, logs = [], []
    for lab in LABS:
        tick = time.perf_counter()
        run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-p", "test*.py", "-v"],
                             cwd=HERE/lab, capture_output=True, text=True, timeout=180)
        output = run.stdout+run.stderr
        matches = re.findall(r"Ran (\d+) tests? in", output)
        count = int(matches[-1]) if matches else 0
        row = {"lab": lab, "test_count": count, "passed": run.returncode == 0 and count > 0,
               "returncode": run.returncode, "seconds": time.perf_counter()-tick}
        results.append(row); logs.append(lab+"\n"+output)
        print(json.dumps(row), flush=True)
    same = before == hashes()
    summary = {"all_tests_passed": same and all(r["passed"] for r in results),
               "test_count": sum(r["test_count"] for r in results), "suite_count": len(results),
               "source_unchanged_during_tests": same, "suites": results,
               "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "seconds": time.perf_counter()-start, "python": sys.version,
               "implementation_sha256": before}
    (HERE/"THRESHOLD_TEST_OUTPUT.txt").write_text("\n".join(logs), encoding="utf-8")
    (HERE/"THRESHOLD_TEST_SUMMARY.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return 0 if summary["all_tests_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
