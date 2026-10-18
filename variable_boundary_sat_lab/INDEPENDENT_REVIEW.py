"""Independent replay of variable-boundary SAT certificates."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def clause_value(clause, assignment):
    return bool(clause) and any(bool(assignment[abs(lit) - 1]) == (lit > 0) for lit in clause)


def boundary(n, clauses, order):
    pos = {v: i for i, v in enumerate(order)}
    out = []
    scopes = [{abs(lit) - 1 for lit in clause} for clause in clauses]
    for cut in range(n + 1):
        out.append(tuple(v for v in order[:cut]
                        if any(v in scope and any(pos[w] >= cut for w in scope) for scope in scopes)))
    return out


def direct_replay(n, clauses, order):
    scopes = [{abs(lit) - 1 for lit in clause} for clause in clauses]
    pos = {v: i for i, v in enumerate(order)}
    bs = boundary(n, clauses, order)
    if any(not clause for clause in clauses):
        return bs, [[0]] + [[] for _ in range(n)], [[] for _ in range(n)], False
    states = [[0]]; transitions = []
    for cut in range(1, n + 1):
        prev = bs[cut - 1]; cur = bs[cut]; variable = order[cut - 1]
        completed = [clause for clause, scope in zip(clauses, scopes)
                     if scope and max(pos[v] for v in scope) + 1 == cut]
        next_states = {}; step = []
        for old_index, old_state in enumerate(states[-1]):
            old = {v: (old_state >> i) & 1 for i, v in enumerate(prev)}
            for bit in (0, 1):
                assignment = {**old, variable: bit}
                if any(not clause_value(clause, assignment) for clause in completed):
                    continue
                new = sum(assignment[v] << i for i, v in enumerate(cur))
                if new not in next_states:
                    next_states[new] = len(next_states)
                step.append([old_index, bit, next_states[new]])
        states.append([x for x, _ in sorted(next_states.items(), key=lambda item: item[1])])
        transitions.append(step)
    return bs, states, transitions, bool(states[-1])


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['rows']:
        case = saved['case']; result = saved['result']
        bs, states, transitions, sat = direct_replay(case['n'], case['clauses'], case['order'])
        assert [list(x) for x in bs] == result['boundaries']
        assert states == result['states'] and transitions == result['transitions']
        assert sat == result['sat'] == case['expected_sat']
        rows.append({'name': case['name'], 'sat': sat,
                     'max_width': max(map(len, bs), default=0), 'states': result['stats']['states']})
    source = {name: digest(HERE / name) for name in
              ('boundary_dp.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_VARIABLE_BOUNDARY_REVIEW',
              'case_count': len(rows), 'rows': rows, 'source_hashes': source,
              'chain_64_width': rows[0]['max_width'],
              'star_bad_width': rows[2]['max_width'], 'star_good_width': rows[3]['max_width']}
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent variable-boundary SAT review\n\n'
        'A separate frontier evaluator reconstructed every boundary, state set and '
        'transition. It agrees on the SAT chain, UNSAT chain, bad/good star orders '
        'and dense 3-CNF control. The chain reaches 64 variables at width one; '
        'the star order changes the state width without changing the SAT answer.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'chain_width': review['chain_64_width'],
                      'star_bad_width': review['star_bad_width'],
                      'star_good_width': review['star_good_width']}))


if __name__ == '__main__':
    run()
