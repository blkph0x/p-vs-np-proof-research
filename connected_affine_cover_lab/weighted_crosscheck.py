"""Weighted-DAG escape route for the connected positive path controls."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "weighted_affine_dag_lab"))

spec = importlib.util.spec_from_file_location("weighted_path_dag", ROOT / "weighted_affine_dag_lab" / "dag.py")
dag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dag
spec.loader.exec_module(dag)

sys.path.insert(0, str(HERE))
import cover

CAPS = dict(max_terms=256, max_products=100000, max_nodes=4096,
            max_work=3000000, max_variables=1024, max_factors=4096,
            max_integer_bits=100000)


def path_factors(n: int):
    return [{'kind': 'or', 'literals': [i + 1, i + 2]} for i in range(n - 1)]


def source_hashes():
    paths = [ROOT / 'weighted_affine_dag_lab' / 'dag.py',
             ROOT / 'affine_boundary_lab' / 'boundary.py', HERE / 'weighted_crosscheck.py']
    return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def run():
    before = source_hashes()
    rows = []
    for n in (8, 16, 32, 64, 128):
        factors = path_factors(n)
        result = dag.solve_factors(n, factors, order=list(range(n - 1)), **CAPS)
        checked = dag.verify_factors(n, factors, result, order=list(range(n - 1)), **CAPS)
        expected = [cover.fib_count(n), 1]
        assert result['status'] == 'EXACT' and result['value'] == expected
        assert checked['valid'] and checked['value'] == expected
        rows.append({'n': n, 'factor_count': len(factors), 'expected': expected,
                     'result': result, 'verification': checked})
    after = source_hashes()
    assert before == after
    payload = {'format': 'connected-path-weighted-crosscheck-v1',
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'exact_count': len(rows),
               'max_peak_terms': max(r['result']['stats']['peak_terms'] for r in rows)}
    (HERE / 'WEIGHTED_RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'WEIGHTED_CROSSCHECK_WRITTEN', 'rows': len(rows),
                      'exact': len(rows), 'max_peak_terms': payload['max_peak_terms']}))


if __name__ == '__main__':
    run()
