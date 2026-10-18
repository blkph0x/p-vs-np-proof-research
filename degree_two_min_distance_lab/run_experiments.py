"""Generate degree-two homogeneous minimum-distance controls."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import random

import degree_two_solver as solver


def fixed_controls():
    return [
        {'name': 'triangle_cycle', 'rows': 3, 'columns': [0b011, 0b110, 0b101]},
        {'name': 'terminal_path', 'rows': 3, 'columns': [0b001, 0b011, 0b110, 0b100]},
        {'name': 'parallel_edges', 'rows': 2, 'columns': [0b11, 0b11, 0b01]},
        {'name': 'forest_no_kernel', 'rows': 4, 'columns': [0b0011, 0b0110, 0b1100]},
        {'name': 'zero_column', 'rows': 3, 'columns': [0, 0b011, 0b110]},
        {'name': 'cycle_beats_terminal_path', 'rows': 4,
         'columns': [0b0011, 0b0110, 0b1100, 0b1001, 0b0001, 0b1000]},
    ]


def randomized_controls(count=96):
    rng = random.Random(20261018)
    rows = []
    for index in range(count):
        row_count = 2 + (index % 4)
        possible = [column for column in range(1 << row_count)
                    if column.bit_count() <= 2]
        column_count = 2 + (index % 7)
        rows.append({'name': f'random_{index:03d}', 'rows': row_count,
                     'columns': [rng.choice(possible) for _ in range(column_count)]})
    return rows


def controls():
    return fixed_controls() + randomized_controls()


def main():
    rows = []
    for control in controls():
        instance = solver.encode(control['rows'], control['columns'])
        solution = solver.solve(instance)
        assert solver.verify_solution(instance, solution)
        rows.append({**control, 'solution': solution})
    payload = {'format': 'degree-two-homogeneous-min-distance-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'all_checks_passed': True,
               'rows': rows,
               'scope': 'Polynomial solver for binary parity-check matrices with column weight at most two.'}
    (solver.ROOT / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'DEGREE_TWO_RESULTS_WRITTEN',
                      'controls': len(rows),
                      'distances': [row['solution']['distance'] for row in rows]}))


if __name__ == '__main__':
    main()
