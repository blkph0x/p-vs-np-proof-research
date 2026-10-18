"""Exact primal-graph order search followed by proof-producing SAT DP."""

from __future__ import annotations

import sys
from pathlib import Path

_VARIABLE_LAB = Path(__file__).resolve().parent.parent / 'variable_boundary_sat_lab'
if str(_VARIABLE_LAB) not in sys.path:
    sys.path.insert(0, str(_VARIABLE_LAB))
import boundary_dp  # noqa: E402


def validate(n, clauses):
    if type(n) is not int or n < 0:
        raise ValueError('nonnegative variable count required')
    if type(clauses) not in (list, tuple):
        raise ValueError('clause list required')
    checked = []
    for clause in clauses:
        if type(clause) not in (list, tuple):
            raise ValueError('clause required')
        row = []
        for literal in clause:
            if type(literal) is not int or literal == 0 or abs(literal) > n:
                raise ValueError('invalid literal')
            row.append(literal)
        checked.append(tuple(row))
    return checked


def scopes(n, clauses):
    clauses = validate(n, clauses)
    return tuple(frozenset(abs(literal) - 1 for literal in clause) for clause in clauses)


def primal_edges(n, clauses):
    """The primal graph joins every pair of variables in one clause."""
    scopes_ = scopes(n, clauses)
    edges = set()
    for scope in scopes_:
        vertices = sorted(scope)
        for left, u in enumerate(vertices):
            for v in vertices[left + 1:]:
                edges.add((u, v))
    return tuple(sorted(edges))


def boundary(n, clauses, subset):
    scopes_ = scopes(n, clauses)
    if type(subset) is not int or subset < 0 or subset >= (1 << n):
        raise ValueError('invalid prefix subset')
    suffix = ((1 << n) - 1) ^ subset
    return tuple(v for v in range(n) if subset >> v & 1 and
                 any(v in scope and any(suffix >> w & 1 for w in scope) for scope in scopes_))


def order_records(n, clauses, order):
    validate(n, clauses)
    if type(order) not in (list, tuple) or sorted(order) != list(range(n)):
        raise ValueError('order must be a permutation')
    subset = 0
    records = [{'cut': 0, 'subset': 0, 'boundary': [], 'width': 0}]
    for cut, variable in enumerate(order, 1):
        subset |= 1 << variable
        current = list(boundary(n, clauses, subset))
        records.append({'cut': cut, 'subset': subset, 'boundary': current,
                        'width': len(current)})
    return records, max((row['width'] for row in records), default=0)


def optimal_order(n, clauses, *, max_subsets=1_000_000):
    """Exact bottleneck subset-DP; returns UNKNOWN when its work cap fires."""
    clauses = validate(n, clauses)
    if type(max_subsets) is not int or max_subsets < 1:
        raise ValueError('positive subset cap required')
    full = (1 << n) - 1
    best = {0: (0, ())}
    for subset in range(1 << n):
        if subset not in best:
            continue
        prior_width, prior_order = best[subset]
        for variable in range(n):
            bit = 1 << variable
            if subset & bit:
                continue
            nxt = subset | bit
            cut_width = 0 if nxt == full else len(boundary(n, clauses, nxt))
            candidate = (max(prior_width, cut_width), prior_order + (variable,))
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
                if len(best) > max_subsets:
                    return {'status': 'UNKNOWN', 'reason': 'subset cap',
                            'state_count': len(best), 'processed_subset': subset}
    width, order = best[full]
    records, replay_width = order_records(n, clauses, order)
    assert width == replay_width
    return {'status': 'EXACT', 'order': list(order), 'width': width,
            'records': records, 'state_count': len(best)}


def solve(n, clauses, *, max_subsets=1_000_000, max_states=1_000_000,
          max_transitions=4_000_000):
    clauses = validate(n, clauses)
    search = optimal_order(n, clauses, max_subsets=max_subsets)
    if search['status'] != 'EXACT':
        return {'status': 'UNKNOWN', 'reason': search['reason'],
                'search': search}
    sat = boundary_dp.solve(n, clauses, search['order'],
                            max_states=max_states, max_transitions=max_transitions)
    if sat['status'] != 'EXACT':
        return {'status': 'UNKNOWN', 'reason': sat['reason'],
                'search': search, 'sat': sat}
    return {'status': 'EXACT', 'sat': sat['sat'], 'order': search['order'],
            'width': search['width'], 'search': search, 'sat_certificate': sat}


def verify(n, clauses, result):
    try:
        clauses = validate(n, clauses)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'valid': False, 'errors': ['missing exact result']}
        order = result['order']
        records, width = order_records(n, clauses, order)
        optimum = optimal_order(n, clauses)
        if optimum['status'] != 'EXACT' or width != result['width'] or width != optimum['width']:
            return {'valid': False, 'errors': ['nonoptimal width']}
        if records != result['search']['records']:
            return {'valid': False, 'errors': ['order certificate mismatch']}
        checked = boundary_dp.verify(n, clauses, result['sat_certificate'])
        if not checked['valid'] or checked['sat'] != result['sat']:
            return {'valid': False, 'errors': ['SAT certificate mismatch']}
        return {'valid': True, 'sat': result['sat'], 'width': width, 'errors': []}
    except (ValueError, KeyError, TypeError, IndexError):
        return {'valid': False, 'errors': ['malformed certificate']}


def brute_sat(n, clauses):
    return boundary_dp.brute_sat(n, clauses)
