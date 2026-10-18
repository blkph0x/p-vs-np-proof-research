"""Independent replay of the dense-redundancy frontier control."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def formula(pairs):
    n = 2 * pairs
    clauses = []
    for pair in range(pairs):
        left, right = 2 * pair, 2 * pair + 1
        clauses.extend([[-(left + 1), right + 1], [left + 1, -(right + 1)]])
    for left in range(n):
        for right in range(left + 1, n):
            clauses.append([left + 1, -(left + 1), right + 1])
    return n, clauses


def strip_tautologies(clauses):
    return [clause for clause in clauses
            if not any(literal > 0 and -literal in clause for literal in clause)]


def direct_solve(n, clauses, order):
    position = {variable: index for index, variable in enumerate(order)}
    scopes = [set(abs(literal) - 1 for literal in clause) for clause in clauses]
    boundaries = []
    for cut in range(n + 1):
        boundaries.append(tuple(variable for variable in range(n)
                                if position[variable] < cut and
                                any(variable in scope and
                                    any(position[other] >= cut for other in scope)
                                    for scope in scopes)))
    last = [0 if not scope else max(position[v] for v in scope) + 1 for scope in scopes]
    states = [[0]]
    transitions = 0
    for cut in range(1, n + 1):
        previous, current = boundaries[cut - 1], boundaries[cut]
        variable = order[cut - 1]
        completed = [index for index, end in enumerate(last) if end == cut]
        next_states = {}
        for old in states[-1]:
            assignment = {v: (old >> i) & 1 for i, v in enumerate(previous)}
            for bit in (0, 1):
                trial = dict(assignment); trial[variable] = bit
                valid = True
                for index in completed:
                    clause = clauses[index]
                    if not clause or not any(trial[abs(lit) - 1] == int(lit > 0) for lit in clause):
                        valid = False
                        break
                if not valid:
                    continue
                state = sum(trial[v] << i for i, v in enumerate(current))
                next_states.setdefault(state, len(next_states))
                transitions += 1
        states.append([state for state, _ in sorted(next_states.items(), key=lambda item: item[1])])
    return {'max_width': max(map(len, boundaries), default=0),
            'states': sum(len(layer) for layer in states), 'transitions': transitions,
            'sat': bool(states[-1])}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    saved = json.loads((HERE / 'REDUNDANCY_ADVERSARY.json').read_text(encoding='utf-8'))
    rows = []
    for saved_row in saved['rows']:
        pairs = saved_row['pairs']; n, dense = formula(pairs)
        clean = strip_tautologies(dense); order = list(range(n))
        raw = direct_solve(n, dense, order)
        normalized = direct_solve(n, clean, order)
        assert raw['max_width'] == saved_row['raw']['max_width']
        assert raw['states'] == saved_row['raw']['states']
        assert raw['transitions'] == saved_row['raw']['transitions']
        assert raw['sat'] == saved_row['sat']
        assert normalized['max_width'] == saved_row['normalized']['max_width']
        assert normalized['states'] == saved_row['normalized']['states']
        assert normalized['transitions'] == saved_row['normalized']['transitions']
        rows.append({'pairs': pairs, 'raw': raw, 'normalized': normalized})
    source = {name: digest(HERE / name) for name in
              ('boundary_dp.py', 'REDUNDANCY_ADVERSARY.py', 'INDEPENDENT_REDUNDANCY_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_REDUNDANCY_REVIEW', 'case_count': len(rows),
              'rows': rows, 'source_hashes': source,
              'largest_raw_states': rows[-1]['raw']['states'],
              'largest_normalized_states': rows[-1]['normalized']['states']}
    (HERE / 'INDEPENDENT_REDUNDANCY_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REDUNDANCY_REVIEW.md').write_text(
        '# Independent redundancy adversary review\n\n'
        'A separate frontier evaluator agrees with every dense and normalized '
        'state count. Tautological clauses force raw width to grow with the '
        'number of variables and produce exponentially many syntactic states, '
        'while removing them restores width one. This is a representation '
        'control, not a hardness claim.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'largest_raw_states': review['largest_raw_states'],
                      'largest_normalized_states': review['largest_normalized_states']}))


if __name__ == '__main__':
    run()
