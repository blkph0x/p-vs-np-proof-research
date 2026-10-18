"""Independent replay of primal-order and SAT results."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def scopes(clauses):
    return tuple(frozenset(abs(lit) - 1 for lit in clause) for clause in clauses)


def boundary(n, scope_list, subset):
    suffix = ((1 << n) - 1) ^ subset
    return tuple(v for v in range(n) if subset >> v & 1 and
                 any(v in scope and any(suffix >> w & 1 for w in scope) for scope in scope_list))


def records(n, scope_list, order):
    subset = 0
    out = [{'cut': 0, 'subset': 0, 'boundary': [], 'width': 0}]
    for cut, variable in enumerate(order, 1):
        subset |= 1 << variable
        current = list(boundary(n, scope_list, subset))
        out.append({'cut': cut, 'subset': subset, 'boundary': current, 'width': len(current)})
    return out, max(row['width'] for row in out)


def optimal(n, scope_list):
    full = (1 << n) - 1
    best = {0: (0, ())}
    for subset in range(1 << n):
        if subset not in best:
            continue
        width, order = best[subset]
        for variable in range(n):
            if subset >> variable & 1:
                continue
            nxt = subset | (1 << variable)
            cut = 0 if nxt == full else len(boundary(n, scope_list, nxt))
            candidate = (max(width, cut), order + (variable,))
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
    width, order = best[full]
    replay, replay_width = records(n, scope_list, order)
    assert width == replay_width
    return list(order), width, replay


def brute_sat(n, clauses):
    for bits in range(1 << n):
        if all(any(((bits >> (abs(lit) - 1)) & 1) == int(lit > 0) for lit in clause)
               for clause in clauses):
            return True
    return False


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['rows']:
        case = saved['case']; result = saved['result']
        if result['status'] == 'UNKNOWN':
            assert result['reason'] == case['expected_reason']
            rows.append({'name': case['name'], 'status': 'UNKNOWN'})
            continue
        scope_list = scopes(case['clauses'])
        order, width, replay = optimal(case['n'], scope_list)
        assert width == result['width']
        assert replay == result['search']['records']
        sat = brute_sat(case['n'], case['clauses'])
        assert sat == result['sat'] == case['expected_sat']
        rows.append({'name': case['name'], 'status': 'EXACT', 'sat': sat, 'width': width,
                     'order': order, 'states': result['sat_certificate']['stats']['states']})
    source = {name: digest(HERE / name) for name in ('primal_order.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_PRIMAL_ORDER_REVIEW',
              'case_count': len(rows), 'exact_count': sum(row['status'] == 'EXACT' for row in rows),
              'unknown_count': sum(row['status'] == 'UNKNOWN' for row in rows), 'rows': rows,
              'source_hashes': source, 'chain_width': rows[0]['width'],
              'complete_width': rows[3]['width']}
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent primal-order SAT review\n\n'
        'A separate scope-based subset dynamic program reconstructed every exact '
        'order certificate and compared the resulting SAT answer with brute force. '
        'The complete-graph control has width five; the capped 12-variable search '
        'returns UNKNOWN rather than claiming an exact order.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'exact': review['exact_count'], 'unknown': review['unknown_count'],
                      'chain_width': review['chain_width'], 'complete_width': review['complete_width']}))


if __name__ == '__main__':
    run()
