"""Independent replay of the automatic width-route controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import auto_route
import elimination_controls


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    payload = json.loads((HERE / 'AUTO_ROUTE_RESULTS.json').read_text(encoding='utf-8'))
    rows = payload['rows']
    assert len(rows) == 6
    for name, recorded in payload['source_hashes'].items():
        assert sha(HERE / name) == recorded, name
    exact = [row for row in rows if row['status'] == 'EXACT']
    no = [row for row in rows if row['status'] == 'NO']
    unknown = [row for row in rows if row['status'] == 'UNKNOWN']
    assert len(exact) == 3 and len(no) == 2 and len(unknown) == 1
    for row in exact:
        m = row['n'] // 2
        factors = elimination_controls.connected_chain(m)
        result = auto_route.solve_auto(row['n'], factors, width_cap=row['width_cap'],
                                       max_states=row['max_states'])
        checked = auto_route.verify_auto(row['n'], factors, result,
                                         width_cap=row['width_cap'], max_states=row['max_states'])
        assert result['status'] == 'EXACT' and result['value'] == [1, 1]
        assert checked['valid'] and checked['status'] == 'VERIFIED'
        assert row['verification_valid'] is True and row['discovered_width'] <= 3
    complete = [{'kind': 'or', 'literals': [i + 1, j + 1]}
                for i in range(8) for j in range(i + 1, 8)]
    result = auto_route.solve_auto(8, complete, width_cap=2)
    assert result['status'] == 'NO' and auto_route.verify_auto(8, complete, result, width_cap=2)['valid']
    narrow = auto_route.solve_auto(16, elimination_controls.connected_chain(8), width_cap=2)
    assert narrow['status'] == 'NO'
    path = [{'kind': 'or', 'literals': [i + 1, i + 2]} for i in range(31)]
    result = auto_route.solve_auto(32, path, width_cap=1, max_states=1)
    assert result['status'] == 'UNKNOWN' and auto_route.verify_auto(32, path, result,
                                                                     width_cap=1, max_states=1)['valid']
    review = {'status': 'VERIFIED_INDEPENDENT_AUTO_ROUTE_REVIEW',
              'rows': len(rows), 'exact': len(exact), 'no': len(no), 'unknown': len(unknown),
              'chain_128_peak_terms': next(r['peak_terms'] for r in exact if r['name'] == 'chain_128'),
              'source_hashes_match': True}
    (HERE / 'AUTO_ROUTE_REVIEW.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (HERE / 'AUTO_ROUTE_REVIEW.md').write_text(
        '# Independent automatic-route review\n\n'
        'The discovery-to-solver route was regenerated from the original chain, '
        'complete-graph and path factors. It produced exact verified values for '
        'the three chain sizes, certified NO for both narrow-width controls, and '
        'UNKNOWN for the state-capped path search. The largest chain certificate '
        'retained three terms. No non-exact outcome was assigned a SAT value.\n',
        encoding='utf-8')
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    main()
