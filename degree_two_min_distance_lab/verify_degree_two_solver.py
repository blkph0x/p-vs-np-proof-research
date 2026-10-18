"""Independent replay and direct exhaustive checks for the degree-two solver."""
from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def encode(rows, columns):
    if type(rows) is not int or rows < 0:
        raise AssertionError('bad row count')
    if any(type(column) is not int or column < 0 or column >> rows or column.bit_count() > 2
           for column in columns):
        raise AssertionError('bad column')
    return rows, tuple(columns)


def syndrome(instance, selection):
    _, columns = instance
    value = 0
    for index in selection:
        value ^= columns[index]
    return value


def brute_force(instance):
    rows, columns = instance
    best = None
    for size in range(1, len(columns) + 1):
        for selection in combinations(range(len(columns)), size):
            if syndrome(instance, selection) == 0:
                best = selection
                break
        if best is not None:
            break
    return None if best is None else {'distance': len(best), 'selected_columns': list(best)}


def verify_solution(instance, solution):
    selected = solution['selected_columns']
    if len(selected) != len(set(selected)) or syndrome(instance, selected) != 0:
        return False
    if solution['distance'] is None:
        return not selected
    return solution['distance'] == len(selected) > 0


def main():
    artifact = json.loads((ROOT / 'RESULTS.json').read_text(encoding='utf-8'))
    assert artifact['all_checks_passed']
    for row in artifact['rows']:
        instance = encode(row['rows'], row['columns'])
        expected = brute_force(instance)
        saved = row['solution']
        assert verify_solution(instance, saved)
        if expected is None:
            assert saved['distance'] is None
        else:
            assert saved['distance'] == expected['distance']
    forged = json.loads(json.dumps(artifact['rows'][0]['solution']))
    forged['distance'] = 1 if forged['distance'] != 1 else 2
    assert not (forged['distance'] == len(forged['selected_columns']) and
                forged['distance'] > 0 and
                verify_solution(encode(artifact['rows'][0]['rows'], artifact['rows'][0]['columns']), forged))
    print(json.dumps({'independent_checks_passed': True,
                      'controls': len(artifact['rows']),
                      'all_bruteforce_matches': True}))


if __name__ == '__main__':
    main()
