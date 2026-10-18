"""Save connected affine-support controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cover


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    exhaustive = [cover.contained_summary(n) for n in range(0, 7)]
    all_size = [cover.verify_path_theorem_instance(n) for n in [1, 2, 8, 16, 32, 64, 128, 256]]
    payload = {
        'schema': 'connected_affine_cover_experiment_v1',
        'family': 'path CNF F_n = AND_i (x_i OR x_(i+1)); satisfying assignments have no adjacent zeros.',
        'interpretation': 'Exact lower bound for nonnegative affine-support decompositions only; no signed or unrestricted SAT hardness claim.',
        'exhaustive_small': exhaustive,
        'all_size_controls': all_size,
        'source_hashes': {name: sha(HERE / name) for name in ['cover.py', 'test_cover.py', 'run_experiments.py']},
    }
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'CONNECTED_AFFINE_CONTROLS_WRITTEN',
                      'small_cases': len(exhaustive), 'all_size_cases': len(all_size),
                      'n256_lower_bound': all_size[-1]['lower_bound_pieces']}, sort_keys=True))


if __name__ == '__main__':
    main()
