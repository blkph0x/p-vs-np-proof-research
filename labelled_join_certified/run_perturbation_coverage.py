"""Save exact dense-U representation-count controls."""
from hashlib import sha256
import json
from pathlib import Path

import perturbation_coverage as coverage


HERE = Path(__file__).resolve().parent


def main():
    cases = [(128, 64, 7), (256, 128, 16), (512, 256, 27), (16, 8, 12)]
    records = [coverage.bound_record(*case) for case in cases]
    sources = {}
    for path in (HERE/'perturbation_coverage.py', HERE/'test_perturbation_coverage.py',
                 HERE/'PERTURBATION_COVERAGE_THEOREM.md', HERE/'run_perturbation_coverage.py',
                 HERE/'verify_perturbation_coverage.py'):
        sources[path.name] = sha256(path.read_bytes()).hexdigest()
    output = {'format': 'dense-u-perturbation-coverage-v1', 'cases': records,
              'source_sha256': sources,
              'interpretation': 'The count concerns same-coordinate B+UV row spaces and allows dense U and V. It excludes universal O(log n) labels for this representation language, not arbitrary SAT algorithms or nonlinear encodings.'}
    (HERE/'PERTURBATION_COVERAGE_RESULTS.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
