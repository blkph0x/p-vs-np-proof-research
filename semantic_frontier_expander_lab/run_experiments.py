"""Generate proof-producing semantic frontier expander controls."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import semantic_frontier as sf


def build_artifact():
    rows = []
    for index, control in enumerate(sf.controls()):
        n, edges = control['n'], control['edges']
        expansion = sf.expansion_certificate(n, edges)
        lower_bound = sf.theorem_lower_bound(
            n, expansion['maximum_degree'], expansion['epsilon_numerator'],
            expansion['epsilon_denominator'])
        orders = []
        for order in sf.sampled_orders(n, 20261018 + index):
            pairs = sf.productive_sequence(n, edges, order)
            separation = sf.verify_residual_separation(n, edges, pairs)
            assert len(pairs) >= lower_bound
            assert sf.verify_productive_sequence(n, edges, order, pairs)
            assert separation['valid']
            orders.append({'order': list(order), 'pairs': [list(pair) for pair in pairs],
                           'productive_width': len(pairs),
                           'separation': separation})
        rows.append({'name': control['name'], 'n': n,
                     'edges': [list(edge) for edge in edges],
                     'expansion': expansion, 'theorem_lower_bound': lower_bound,
                     'sampled_orders': orders})
    return {'format': 'semantic-frontier-expander-v1',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'all_checks_passed': True,
            'theorem': 'bounded-degree expansion implies linear productive width and 2^width residual functions',
            'rows': rows,
            'scope': 'Graph-CNF semantic frontier/OBDD lower-bound controls; not a P-versus-NP proof.'}


def main():
    artifact = build_artifact()
    (sf.ROOT / 'RESULTS.json').write_text(json.dumps(artifact, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'SEMANTIC_FRONTIER_RESULTS_WRITTEN',
                      'controls': len(artifact['rows']),
                      'minimum_productive_width': min(
                          row['theorem_lower_bound'] for row in artifact['rows'])}))


if __name__ == '__main__':
    main()
