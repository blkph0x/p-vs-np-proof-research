"""Independent replay of natural-generator objective defects."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'objective_pullback_limits'
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from explicit_code_family import digest_columns, generate_columns, parameters
from objective_pullback import verify


def direct_objective(rows, z):
    return sum((row & z).bit_count() & 1 for row in rows)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'EXPLICIT_OBJECTIVE_PULLBACK_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'EXPLICIT_OBJECTIVE_PULLBACK_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]
    reviewed = []
    for record in payload['records']:
        k = record['field_degree']
        spec = parameters(k)
        _, rows = generate_columns(k)
        assert len(rows) == record['columns'] == spec['columns']
        assert digest_columns(rows, spec['binary_rank']) == record['column_digest']
        j, m = record['pair']
        values = [direct_objective(rows, 1 << j),
                  direct_objective(rows, 1 << m),
                  direct_objective(rows, (1 << j) | (1 << m))]
        assert values == record['values']
        defect = values[0] + values[1] - values[2]
        assert defect == record['defect'] > 0
        checked = verify(rows, spec['binary_rank'], [1] * len(rows), {
            'status': 'EXACT', 'format': 'linear_cost_pullback_v1',
            'input_hash': record['input_hash'], 'additive': False,
            'pair': record['pair'], 'values': values, 'defect': defect})
        assert checked['valid']
        reviewed.append({'field_degree': k, 'pair': record['pair'],
                         'values': values, 'defect': defect})
    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'explicit_objective_pullback.py',
               'run_explicit_objective_pullback.py',
               'EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_EXPLICIT_OBJECTIVE_PULLBACK',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'source_hashes': source,
        'scope': 'Natural free-message generator map only; no claim about constrained or nonlinear encodings.',
    }
    (HERE / 'EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.md').write_text(
        '# Independent natural-generator objective review\n\n'
        'For each explicit code family, direct three-assignment evaluation '
        'reproduces a positive additivity defect. Therefore fixed nonnegative '
        'unary costs on the free message bits cannot equal the codeword Hamming '
        'weight on all messages. This closes only the natural linear generator '
        'shortcut; constrained and nonlinear maps remain outside scope.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'defects': [row['defect'] for row in reviewed]}))


if __name__ == '__main__':
    run()
