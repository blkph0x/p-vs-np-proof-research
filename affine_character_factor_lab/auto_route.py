"""End-to-end bounded route: discover width, then run and replay the DAG."""

from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import elimination_controls as elimination
import order_discovery
import run_order_controls


def _caps(caps):
    selected = dict(elimination.CAPS)
    if caps:
        selected.update(caps)
    return selected


def solve_auto(n, factors, *, width_cap, max_states=100_000, caps=None):
    """Return EXACT only after both discovery and weighted replay succeed."""
    scopes = run_order_controls.scopes_for(factors)
    discovered = order_discovery.find_order(n, scopes, width_cap,
                                            max_states=max_states)
    base = {'discovery': discovered, 'width_cap': width_cap,
            'max_states': max_states}
    if discovered['status'] != 'EXACT':
        return {'status': discovered['status'],
                'reason': discovered.get('reason'), **base}
    factor_order = order_discovery.factor_order_from_variable_order(
        scopes, discovered['order'])
    selected = _caps(caps)
    weighted = elimination.dag.solve_factors(n, factors, order=factor_order,
                                             **selected)
    if weighted['status'] != 'EXACT':
        return {'status': 'UNKNOWN', 'reason': weighted.get('reason'),
                'factor_order': factor_order, 'weighted_status': weighted['status'],
                **base}
    checked = elimination.dag.verify_factors(n, factors, weighted,
                                             order=factor_order, **selected)
    if not checked.get('valid'):
        return {'status': 'INVALID', 'reason': 'weighted certificate rejected',
                'factor_order': factor_order, 'weighted_status': weighted['status'],
                'weighted_verification': checked, **base}
    return {'status': 'EXACT', 'value': weighted['value'],
            'factor_order': factor_order, 'weighted_result': weighted,
            'weighted_verification': checked, **base}


def verify_auto(n, factors, result, *, width_cap, max_states=100_000, caps=None):
    """Recompute discovery and verify the embedded weighted certificate."""
    if type(result) is not dict:
        return {'valid': False, 'status': 'INVALID', 'errors': ['result schema']}
    scopes = run_order_controls.scopes_for(factors)
    discovered = order_discovery.find_order(n, scopes, width_cap,
                                            max_states=max_states)
    if result.get('status') != discovered.get('status'):
        return {'valid': False, 'status': 'INVALID', 'errors': ['discovery status mismatch']}
    if discovered['status'] != 'EXACT':
        if 'value' in result:
            return {'valid': False, 'status': 'INVALID', 'errors': ['value on non-exact discovery']}
        return {'valid': True, 'status': discovered['status'], 'errors': []}
    order = order_discovery.factor_order_from_variable_order(scopes, discovered['order'])
    if result.get('factor_order') != order:
        return {'valid': False, 'status': 'INVALID', 'errors': ['factor order mismatch']}
    weighted = result.get('weighted_result')
    if type(weighted) is not dict:
        return {'valid': False, 'status': 'INVALID', 'errors': ['missing weighted certificate']}
    checked = elimination.dag.verify_factors(n, factors, weighted, order=order,
                                             **_caps(caps))
    if not checked.get('valid'):
        return {'valid': False, 'status': checked.get('status', 'INVALID'),
                'errors': checked.get('errors', [])}
    if result.get('value') != weighted.get('value'):
        return {'valid': False, 'status': 'INVALID', 'errors': ['value mismatch']}
    return {'valid': True, 'status': 'VERIFIED', 'errors': [],
            'weighted_verification': checked}
