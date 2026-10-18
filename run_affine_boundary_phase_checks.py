"""Run the new compact-boundary suites and bind their frozen source files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LABS = ('affine_boundary_lab', 'affine_boundary_reference', 'weighted_affine_dag_lab', 'original_count_reference_lab')


def hashes():
    paths = [Path(__file__).resolve()]
    for lab in LABS:
        paths.extend(p for p in sorted((HERE/lab).glob('*.py')) if not p.name.startswith('independent_review'))
    return {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    before = hashes()
    started, tick = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    rows, logs = [], []
    for lab in LABS:
        start = time.perf_counter()
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-p', 'test*.py', '-v'],
                                cwd=HERE/lab, capture_output=True, text=True, timeout=180)
        output = result.stdout+result.stderr
        matches = re.findall(r'Ran (\d+) tests? in', output)
        count = int(matches[-1]) if matches else 0
        row = dict(lab=lab, test_count=count, passed=result.returncode == 0 and count > 0,
                   returncode=result.returncode, seconds=time.perf_counter()-start)
        rows.append(row); logs.append(lab+'\n'+output)
        print(json.dumps(row), flush=True)
    same = before == hashes()
    report = dict(all_tests_passed=same and all(r['passed'] for r in rows),
                  test_count=sum(r['test_count'] for r in rows), suite_count=len(rows),
                  source_unchanged_during_tests=same, suites=rows,
                  started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  seconds=time.perf_counter()-tick, python=sys.version, implementation_sha256=before)
    (HERE/'AFFINE_BOUNDARY_TEST_OUTPUT.txt').write_text('\n'.join(logs), encoding='utf-8')
    (HERE/'AFFINE_BOUNDARY_TEST_SUMMARY.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if report['all_tests_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
