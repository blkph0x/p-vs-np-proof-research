"""Run isolated representation-limit checks; retain the earlier solver runs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
LABS = ("projection_limits", "gadget_limits", "objective_pullback_limits",
        "matching_gadget_limits", "matching_composition_controls")


def hashes():
    paths = [Path(__file__).resolve()]
    for lab in LABS:
        paths.extend(sorted((HERE / lab).glob("*.py")))
    return {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def main():
    started = datetime.now(timezone.utc).isoformat()
    before = hashes()
    results, logs = [], []
    start = time.perf_counter()
    for lab in LABS:
        tick = time.perf_counter()
        if not list((HERE / lab).glob("test*.py")):
            raise RuntimeError("missing audit tests: " + lab)
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-p", "test*.py", "-v"],
            cwd=HERE / lab, capture_output=True, text=True, timeout=180)
        output = completed.stdout + completed.stderr
        counts = re.findall(r"Ran (\d+) tests? in", output)
        count = int(counts[-1]) if counts else 0
        results.append({"lab": lab, "passed": completed.returncode == 0 and count > 0,
                        "returncode": completed.returncode, "test_count": count,
                        "seconds": time.perf_counter() - tick})
        logs.append(lab + "\n" + output)
        print(json.dumps(results[-1]), flush=True)
    after = hashes()
    same = before == after
    passed = same and all(item["passed"] for item in results)
    summary = {"all_tests_passed": passed, "source_unchanged_during_tests": same,
               "test_count": sum(item["test_count"] for item in results),
               "suite_count": len(results), "suites": results,
               "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "seconds": time.perf_counter() - start, "python": sys.version,
               "implementation_sha256": before}
    (HERE / "FOLLOWUP_TEST_OUTPUT.txt").write_text("\n".join(logs), encoding="utf-8")
    (HERE / "FOLLOWUP_TEST_SUMMARY.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
