"""Generate exact mixed-frontier controls and save the full residual evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import mixed_frontier as mf

HERE = Path(__file__).resolve().parent


def cases():
    all12 = list(range(12))
    return [
        {"name": "duplicate_parity_6", "n": 12,
         "constraints": [{"kind": "parity", "scope": all12, "rhs": 0} for _ in range(6)], "cut": 6,
         "expected_classes": 2},
        {"name": "independent_crossing_parity_6", "n": 12,
         "constraints": [{"kind": "parity", "scope": [i, 6 + i], "rhs": 0} for i in range(6)], "cut": 6,
         "expected_classes": 64},
        {"name": "same_scope_cardinality_plus_parity", "n": 12,
         "constraints": [{"kind": "cardinality", "scope": all12, "op": "eq", "target": 6},
                         {"kind": "parity", "scope": all12, "rhs": 0}], "cut": 6,
         "expected_classes": 7},
        {"name": "duplicate_cardinality_5", "n": 12,
         "constraints": [{"kind": "cardinality", "scope": all12, "op": "eq", "target": 6} for _ in range(5)], "cut": 6,
         "expected_classes": 7},
        {"name": "partial_scope_cardinality_plus_parity", "n": 12,
         "constraints": [{"kind": "cardinality", "scope": all12, "op": "eq", "target": 6},
                         {"kind": "parity", "scope": [0, 1, 2, 6, 7, 8], "rhs": 0}], "cut": 6,
         "expected_classes": 10},
        {"name": "clause_gate_plus_parity", "n": 12,
         "constraints": [{"kind": "clause", "literals": [i + 1, 7 + i]} for i in range(6)]
                        + [{"kind": "parity", "scope": all12, "rhs": 0}], "cut": 6,
         "expected_classes": None},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {p.name: digest(p) for p in (HERE / 'mixed_frontier.py', HERE / 'run_experiments.py')}
    rows = []
    for case in cases():
        row = mf.analyze_cut(case['n'], case['constraints'], case['cut'])
        if case['expected_classes'] is not None:
            assert row['future_classes'] == case['expected_classes'], case['name']
        rows.append({'case': {**case, 'constraints': mf.jsonable_constraints(case['constraints'])}, 'analysis': row})
    after = {p.name: digest(p) for p in (HERE / 'mixed_frontier.py', HERE / 'run_experiments.py')}
    assert before == after
    payload = {'format': 'mixed-information-frontier-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'cases': rows,
               'case_count': len(rows),
               'max_naive_product': max(r['analysis']['naive_product_states'] for r in rows),
               'max_future_classes': max(r['analysis']['future_classes'] for r in rows)}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'MIXED_FRONTIER_RESULTS_WRITTEN', 'cases': len(rows),
                      'max_naive_product': payload['max_naive_product'],
                      'max_future_classes': payload['max_future_classes']}))


if __name__ == '__main__':
    run()
