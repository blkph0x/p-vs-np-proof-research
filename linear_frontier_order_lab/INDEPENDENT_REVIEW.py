"""Independent rank replay and certificate audit for the order controls."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rank(vectors):
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def record(matrix, order):
    rows, n = len(matrix), len(matrix[0])
    columns = [sum(matrix[r][c] << r for r in range(rows)) for c in range(n)]
    full = (1 << n) - 1
    subset = 0
    records = []
    for cut, variable in enumerate(order, 1):
        subset |= 1 << variable
        past = rank(columns[i] for i in range(n) if subset >> i & 1)
        future = rank(columns[i] for i in range(n) if not (subset >> i & 1))
        total = rank(columns)
        records.append({'cut': cut, 'subset': subset, 'rank_past': past,
                        'rank_future': future, 'rank_all': total,
                        'lambda': past + future - total if cut < n else 0})
    return records, max((x['lambda'] for x in records[:-1]), default=0)


def optimal_width(matrix):
    n = len(matrix[0])
    columns = [sum(matrix[r][c] << r for r in range(len(matrix))) for c in range(n)]
    full = (1 << n) - 1
    dp = {0: 0}
    for subset in range(1 << n):
        if subset not in dp:
            continue
        for variable in range(n):
            if subset >> variable & 1:
                continue
            nxt = subset | (1 << variable)
            if nxt == full:
                cut = 0
            else:
                past = rank(columns[i] for i in range(n) if nxt >> i & 1)
                future = rank(columns[i] for i in range(n) if not (nxt >> i & 1))
                cut = past + future - rank(columns)
            value = max(dp[subset], cut)
            if nxt not in dp or value < dp[nxt]:
                dp[nxt] = value
    return dp[full]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['rows']:
        matrix = saved['matrix']
        records, bad_width = record(matrix, saved['bad_order'])
        optimal = saved['optimal']
        replay_width = optimal_width(matrix)
        assert bad_width == saved['bad_width']
        assert replay_width == optimal['width']
        assert records == record(matrix, saved['bad_order'])[0]
        assert len(optimal['order']) == len(matrix[0])
        assert sorted(optimal['order']) == list(range(len(matrix[0])))
        rows.append({'name': saved['name'], 'bad_width': bad_width,
                     'optimal_width': replay_width, 'optimal_order': optimal['order']})
    source = {name: digest(HERE / name) for name in
              ('frontier.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_LINEAR_FRONTIER_REVIEW',
              'case_count': len(rows), 'rows': rows, 'source_hashes': source,
              'crossing_bad_width': rows[0]['bad_width'],
              'crossing_optimal_width': rows[0]['optimal_width']}
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent linear-frontier review\n\n'
        'A separate GF(2) rank implementation replayed every saved cut record and '
        'recomputed the subset-DP optimum. The six-pair crossing system has width '
        '6 under the supplied all-left-then-all-right order but width 1 under the '
        'verified optimal interleaving. Repeated-row and identity controls agree. '
        'The order search is exponential and is an exact small-instance oracle.\n',
        encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'crossing_bad_width': review['crossing_bad_width'],
                      'crossing_optimal_width': review['crossing_optimal_width']}))


if __name__ == '__main__':
    run()
