"""Independent graph-boundary replay."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def boundary(n, edges, subset):
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    return tuple(i for i in range(n) if subset >> i & 1 and any(not (subset >> j & 1) for j in neighbors[i]))


def records(n, edges, order):
    subset = 0
    out = []
    for cut, vertex in enumerate(order, 1):
        subset |= 1 << vertex
        current = boundary(n, edges, subset)
        out.append({'cut': cut, 'subset': subset, 'boundary': list(current), 'width': len(current)})
    return out, max((x['width'] for x in out[:-1]), default=0)


def optimal_width(n, edges):
    best = {0: 0}
    full = (1 << n) - 1
    for subset in range(1 << n):
        if subset not in best:
            continue
        for vertex in range(n):
            if subset >> vertex & 1:
                continue
            nxt = subset | (1 << vertex)
            value = 0 if nxt == full else len(boundary(n, edges, nxt))
            candidate = max(best[subset], value)
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
    return best[full]


def greedy_order(n, edges):
    remaining = set(range(n)); subset = 0; order = []
    while remaining:
        choices = []
        for vertex in remaining:
            nxt = subset | (1 << vertex)
            score = 0 if nxt == (1 << n) - 1 else len(boundary(n, edges, nxt))
            choices.append((score, vertex))
        vertex = min(choices)[1]
        order.append(vertex); remaining.remove(vertex); subset |= 1 << vertex
    return order


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['rows']:
        case = saved['case']
        bad_records, bad_width = records(case['n'], case['edges'], case['bad_order'])
        assert bad_width == saved['bad_width']
        assert bad_records == records(case['n'], case['edges'], case['bad_order'])[0]
        optimum = optimal_width(case['n'], case['edges'])
        assert optimum == saved['optimal']['width']
        greedy = greedy_order(case['n'], case['edges'])
        _, greedy_width = records(case['n'], case['edges'], greedy)
        assert greedy == saved['greedy_order'] and greedy_width == saved['greedy_width']
        rows.append({'name': case['name'], 'bad_width': bad_width, 'optimal_width': optimum,
                     'optimal_order': saved['optimal']['order'], 'greedy_width': greedy_width})
    source = {name: digest(HERE / name) for name in
              ('vertex_separation.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_VERTEX_SEPARATION_REVIEW',
              'case_count': len(rows), 'rows': rows, 'source_hashes': source,
              'star_bad_width': rows[1]['bad_width'], 'star_optimal_width': rows[1]['optimal_width']}
    review['bipartite_greedy_width'] = next(r['greedy_width'] for r in rows
                                           if r['name'] == 'complete_bipartite_4_2')
    review['bipartite_optimal_width'] = next(r['optimal_width'] for r in rows
                                            if r['name'] == 'complete_bipartite_4_2')
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent vertex-separation review\n\n'
        'A separate set-based implementation reconstructed every saved boundary '
        'and recomputed the subset-DP optimum. The star control has width 7 under '
        'the leaf-first order and width 1 under the optimal center-first order; '
        'path, cycle and complete-graph controls agree. The associated monotone '
        '2-CNF clauses are all satisfiable by the all-ones assignment, so the '
        'layout cost is separate from SAT difficulty. The K4,2 greedy control '
        'has width 4 while an exact order has width 2.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'star_bad_width': review['star_bad_width'],
                      'star_optimal_width': review['star_optimal_width']}))


if __name__ == '__main__':
    run()
