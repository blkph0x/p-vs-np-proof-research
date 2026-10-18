"""Reproduce this follow-up's tests without changing the prior frozen checkpoint."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parent


def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.py'))}


def main():
    before, start = hashes(), perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    run = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'],
                         cwd=ROOT, text=True, capture_output=True, timeout=300)
    elapsed, after = perf_counter() - start, hashes()
    transcript = run.stdout + run.stderr
    match = re.search(r'Ran (\d+) tests? in', transcript)
    summary = {'all_tests_passed': run.returncode == 0 and before == after,
               'returncode': run.returncode, 'test_count': int(match.group(1)) if match else None,
               'source_unchanged_during_tests': before == after, 'seconds': elapsed,
               'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
               'python': sys.version, 'implementation_sha256': after}
    (ROOT / 'TEST_OUTPUT.txt').write_text(transcript, encoding='utf-8')
    (ROOT / 'TEST_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(transcript)
    print(json.dumps({k: v for k, v in summary.items() if k != 'implementation_sha256'}, indent=2))
    return 0 if summary['all_tests_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
