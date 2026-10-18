"""Independent circuit truth-table and frontier-scope replay."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def direct_weight(forms, assignment):
    return sum((form & assignment).bit_count() & 1 for form in forms)


def direct_gate_values(circuit, assignment):
    values = {1 + bit: (assignment >> bit) & 1 for bit in range(circuit['dimension'])}
    for gate in circuit['gates']:
        kind, output = gate[:2]
        if kind == 'const':
            values[output] = gate[2]
        elif kind == 'xor':
            values[output] = values[gate[2]] ^ values[gate[3]]
        elif kind == 'and':
            values[output] = values[gate[2]] & values[gate[3]]
        elif kind == 'not':
            values[output] = 1 ^ values[gate[2]]
        elif kind == 'or':
            values[output] = values[gate[2]] | values[gate[3]]
        else:
            raise AssertionError('unknown gate')
    return values


def clause_ok(clause, values):
    return any((literal > 0) == bool(values[abs(literal)]) for literal in clause)


def independent_boundary(n, clauses, order):
    position = {variable + 1: index for index, variable in enumerate(order)}
    result = []
    for cut in range(n + 1):
        live = []
        for variable in range(1, n + 1):
            if position[variable] >= cut:
                continue
            scope = {abs(literal) for clause in clauses for literal in clause
                     if variable in {abs(item) for item in clause}}
            if any(position[other] >= cut for other in scope):
                live.append(variable)
        result.append(tuple(live))
    return result


def independent_optimal_width(n, clauses):
    """Subset DP replay with an independent boundary representation."""
    scopes = [frozenset(abs(literal) - 1 for literal in clause) for clause in clauses]
    full = (1 << n) - 1
    boundaries = {}
    for subset in range(1 << n):
        suffix = full ^ subset
        boundaries[subset] = sum(
            1 for variable in range(n)
            if subset >> variable & 1 and any(
                variable in scope and any(suffix >> other & 1 for other in scope)
                for scope in scopes))
    best = {0: 0}
    for subset in range(1 << n):
        if subset not in best:
            continue
        for variable in range(n):
            if subset >> variable & 1:
                continue
            nxt = subset | (1 << variable)
            width = max(best[subset], 0 if nxt == full else boundaries[nxt])
            if nxt not in best or width < best[nxt]:
                best[nxt] = width
    return best[full], len(best)


def direct_minimum_nonzero_weight(forms, dimension):
    values = [sum((form & assignment).bit_count() & 1 for form in forms)
              for assignment in range(1, 1 << dimension)]
    return min(values)


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'CIRCUIT_BOUNDARY_CHECK_PASS'
    forms = tuple(payload['forms'])
    circuit = payload['circuit']
    queries = payload['queries']
    assert payload['summary']['assignments'] == 32
    widths = independent_boundary(circuit['variables'], circuit['clauses'], circuit['order'])
    assert max(map(len, widths)) == payload['summary']['max_width']
    order_control = payload['order_control']
    assert order_control == {
        'forms': [1, 2, 3], 'dimension': 3, 'variables': 18, 'clauses': 48,
        'topological_width': 6, 'optimal_width': 4,
        'subset_state_count': 262144, 'optimal_order': order_control['optimal_order']}
    independent_width, independent_states = independent_optimal_width(
        order_control['variables'],
        __import__('circuit_cnf').build_circuit((1, 2, 3), 3)['clauses'])
    assert independent_width == order_control['optimal_width']
    assert independent_states == order_control['subset_state_count']
    distance = payload['distance_control']
    assert tuple(distance['forms']) == (1, 2, 3, 4, 5, 6, 7)
    assert distance['minimum_nonzero_weight'] == direct_minimum_nonzero_weight(
        tuple(distance['forms']), distance['dimension']) == 4
    assert [row['sat'] for row in distance['queries']] == [False, False, False, False, True]
    assert all(row['max_width'] > 0 for row in distance['queries'])
    compact_circuits = distance['compact_circuits']
    assert len(compact_circuits) == 5
    for compact, threshold in zip(compact_circuits, range(5)):
        accept = compact['comparator']['accept_variable']
        for assignment in range(1 << distance['dimension']):
            values = direct_gate_values(compact, assignment)
            assert all(clause_ok(clause, values) for clause in compact['clauses'][:-1])
            output = sum(values[variable] << bit
                         for bit, variable in enumerate(compact['output_bits']))
            assert bool(values[accept]) == (output <= threshold)
    for row in queries:
        assignment = row['assignment']
        values = direct_gate_values(circuit, assignment)
        assert all(clause_ok(clause, values) for clause in circuit['clauses'])
        output = sum(values[variable] << bit
                     for bit, variable in enumerate(circuit['output_bits']))
        assert output == direct_weight(forms, assignment) == row['target']
        assert row['wrong_target'] != output
    source = {name: digest(HERE / name) for name in
              ('circuit_cnf.py', 'run_experiments.py',
               'INDEPENDENT_REVIEW.py', 'THEOREM.md')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_CIRCUIT_BOUNDARY',
        'assignments_checked': len(queries),
        'gate_clauses_checked': len(circuit['clauses']),
        'max_width': max(map(len, widths)),
        'all_gate_truth_tables_checked': True,
        'all_outputs_match_direct_weight': True,
        'all_wrong_targets_rejected_by_producer': True,
        'source_hashes': source,
        'scope': 'Pinned small circuit CNF controls only; no general SAT or P-versus-NP claim.',
    }
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent circuit-boundary review\n\n'
        'The separate evaluator checks every XOR, AND and constant clause for '
        'all 32 source assignments and reproduces every output Hamming weight. '
        'The saved frontier widths are independently recomputed from clause '
        'scopes; the producer rejects every deliberately wrong pinned output. '
        'This verifies the circuit-to-CNF bridge on the bounded control only.\n',
        encoding='utf-8')
    print(json.dumps({'status': review['status'],
                      'assignments': review['assignments_checked'],
                      'max_width': review['max_width']}))


if __name__ == '__main__':
    run()
