"""Proof-producing SAT DP for a supplied variable order and boundary width."""

from __future__ import annotations


def validate(n, clauses, order):
    if type(n) is not int or n < 0:
        raise ValueError('variable count required')
    if type(clauses) not in (list, tuple):
        raise ValueError('clause list required')
    checked = []
    for clause in clauses:
        if type(clause) not in (list, tuple) or any(type(x) is not int or x == 0 or abs(x) > n for x in clause):
            raise ValueError('invalid clause')
        checked.append(tuple(clause))
    if type(order) not in (list, tuple) or sorted(order) != list(range(n)):
        raise ValueError('order must be a variable permutation')
    return checked, list(order)


def clause_value(clause, assignment):
    if not clause:
        return False
    for literal in clause:
        variable = abs(literal) - 1
        if variable not in assignment:
            raise ValueError('clause variable missing from frontier state')
        if bool(assignment[variable]) == (literal > 0):
            return True
    return False


def boundaries(n, clauses, order):
    position = {variable: index for index, variable in enumerate(order)}
    output = []
    for cut in range(n + 1):
        current = []
        for variable in range(n):
            if position[variable] >= cut:
                continue
            if any(variable in {abs(literal) - 1 for literal in clause}
                   and any(position[abs(other) - 1] >= cut for other in clause)
                   for clause in clauses):
                current.append(variable)
        output.append(tuple(current))
    return output


def solve(n, clauses, order, *, max_states=1_000_000, max_transitions=4_000_000):
    clauses, order = validate(n, clauses, order)
    if type(max_states) is not int or max_states < 0 or type(max_transitions) is not int or max_transitions < 0:
        raise ValueError('nonnegative caps required')
    cut_boundaries = boundaries(n, clauses, order)
    if any(not clause for clause in clauses):
        # The empty clause is a contradiction before any variable is assigned.
        # Keep a complete-shaped certificate so replay can verify every cut.
        empty_states = [[0]] + [[] for _ in range(n)]
        return {'status': 'EXACT', 'sat': False, 'order': order,
                'boundaries': [list(b) for b in cut_boundaries],
                'states': empty_states, 'transitions': [[] for _ in range(n)],
                'stats': {'max_width': max(map(len, cut_boundaries), default=0),
                          'states': 1, 'transitions': 0}}
    position = {variable: index for index, variable in enumerate(order)}
    last = []
    for clause in clauses:
        if not clause:
            last.append(0)
        else:
            last.append(max(position[abs(literal) - 1] for literal in clause) + 1)
    states = [[0]]
    transitions = []
    total_states = 1
    total_transitions = 0
    for cut in range(1, n + 1):
        previous_boundary = cut_boundaries[cut - 1]
        current_boundary = cut_boundaries[cut]
        variable = order[cut - 1]
        completed = [index for index, end in enumerate(last) if end == cut]
        next_states = {}
        next_transitions = []
        for old_index, old_state in enumerate(states[-1]):
            old_assignment = {v: (old_state >> i) & 1 for i, v in enumerate(previous_boundary)}
            for bit in (0, 1):
                assignment = dict(old_assignment)
                assignment[variable] = bit
                if any(not clause_value(clauses[index], assignment) for index in completed):
                    continue
                new_state = sum(((assignment[v] & 1) << i) for i, v in enumerate(current_boundary))
                if new_state not in next_states:
                    next_states[new_state] = len(next_states)
                next_index = next_states[new_state]
                next_transitions.append([old_index, bit, next_index])
                total_transitions += 1
                if total_transitions > max_transitions:
                    return {'status': 'UNKNOWN', 'reason': 'transition cap', 'order': order,
                            'boundaries': [list(b) for b in cut_boundaries], 'stats': {
                                'max_width': max(map(len, cut_boundaries), default=0),
                                'states': total_states, 'transitions': total_transitions}}
        states.append([state for state, _ in sorted(next_states.items(), key=lambda item: item[1])])
        transitions.append(next_transitions)
        total_states += len(states[-1])
        if total_states > max_states:
            return {'status': 'UNKNOWN', 'reason': 'state cap', 'order': order,
                    'boundaries': [list(b) for b in cut_boundaries], 'stats': {
                        'max_width': max(map(len, cut_boundaries), default=0),
                        'states': total_states, 'transitions': total_transitions}}
    return {'status': 'EXACT', 'sat': bool(states[-1]), 'order': order,
            'boundaries': [list(b) for b in cut_boundaries],
            'states': states, 'transitions': transitions,
            'stats': {'max_width': max(map(len, cut_boundaries), default=0),
                      'states': total_states, 'transitions': total_transitions}}


def verify(n, clauses, result):
    try:
        clauses, order = validate(n, clauses, result['order'])
        if result.get('status') != 'EXACT':
            return {'valid': False, 'errors': ['non-exact result']}
        expected = solve(n, clauses, order)
        for key in ('boundaries', 'states', 'transitions', 'sat'):
            if result.get(key) != expected.get(key):
                return {'valid': False, 'errors': ['certificate mismatch: ' + key]}
        if result.get('stats') != expected.get('stats'):
            return {'valid': False, 'errors': ['statistics mismatch']}
        return {'valid': True, 'sat': expected['sat'], 'max_width': expected['stats']['max_width'], 'errors': []}
    except (ValueError, KeyError, TypeError, IndexError):
        return {'valid': False, 'errors': ['malformed certificate']}


def brute_sat(n, clauses):
    clauses, _ = validate(n, clauses, list(range(n)))
    for assignment_bits in range(1 << n):
        assignment = {v: (assignment_bits >> v) & 1 for v in range(n)}
        if all(clause_value(clause, assignment) for clause in clauses):
            return True
    return False
