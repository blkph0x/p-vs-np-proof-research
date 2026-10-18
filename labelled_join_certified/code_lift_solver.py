"""Bind certified labelled joins to an original binary parity-check problem.

The supplied invertible row change must produce graph incidence rows followed
by p arbitrary label rows. Homogeneous nonzero optimization then needs only
zero/two-terminal joins through edge pinning. Arbitrary affine targets use the
terminal-subset DP and can still cost exponentially many terminal states.
"""
from time import perf_counter

from labelled_tjoin import solve_tjoin, solve_nonempty, verify_tjoin, verify_nonempty


def _rank(rows):
    basis = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in basis:
                value ^= basis[bit]
            else:
                basis[bit] = value
                break
    return len(basis)


def prepare_code(check_rows, n, graph_rows, *, row_transform=None, target=0,
                 require_nonzero=True, weights=None):
    if type(n) is not int or n < 0:
        raise ValueError('n must be a nonnegative integer')
    original = tuple(check_rows)
    r = len(original)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in original):
        raise ValueError('checks must be nonnegative n-bit rows')
    if type(graph_rows) is not int or not 0 <= graph_rows <= r:
        raise ValueError('graph_rows must be an initial row count')
    if type(target) is not int or target < 0 or target.bit_length() > r:
        raise ValueError('target must refer to original check rows')
    if type(require_nonzero) is not bool:
        raise ValueError('require_nonzero must be Boolean')
    transform = tuple(1 << i for i in range(r)) if row_transform is None else tuple(row_transform)
    if len(transform) != r or any(type(row) is not int or row < 0 or row.bit_length() > r for row in transform) or _rank(transform) != r:
        raise ValueError('row transform must be square and invertible')
    weights = (1,) * n if weights is None else tuple(weights)
    if len(weights) != n or any(type(w) is not int or w < 0 for w in weights):
        raise ValueError('weights must be nonnegative integers for every original coordinate')
    rows, rhs = [], 0
    for i, combination in enumerate(transform):
        row = 0
        for j, original_row in enumerate(original):
            if combination >> j & 1:
                row ^= original_row
        rows.append(row)
        rhs |= ((combination & target).bit_count() % 2) << i
    edges = []
    for j in range(n):
        ends = [i for i in range(graph_rows) if rows[i] >> j & 1]
        label = sum(((row >> j) & 1) << k for k, row in enumerate(rows[graph_rows:]))
        if len(ends) > 2:
            raise ValueError('transformed graph column has weight above two')
        u, v = ((graph_rows, graph_rows) if not ends else
                (ends[0], graph_rows) if len(ends) == 1 else tuple(ends))
        edges.append((u, v, label, weights[j]))
    terminals = [i for i in range(graph_rows) if rhs >> i & 1]
    if len(terminals) % 2:
        terminals.append(graph_rows)
    return {'original_rows': original, 'row_transform': transform, 'rows': tuple(rows),
            'n': n, 'dimension': n - _rank(original), 'graph_rows': graph_rows,
            'label_rows': r - graph_rows, 'vertices': graph_rows + 1,
            'edges': tuple(edges), 'weights': weights, 'transformed_target': rhs,
            'terminals': tuple(terminals), 'label_target': rhs >> graph_rows}


def solve_code(check_rows, n, graph_rows, *, row_transform=None, target=0,
               require_nonzero=True, weights=None, limits=None, max_pin_cases=256):
    started = perf_counter()
    prepared = prepare_code(check_rows, n, graph_rows, row_transform=row_transform,
                            target=target, require_nonzero=require_nonzero, weights=weights)
    arguments = dict(terminals=prepared['terminals'], target=prepared['label_target'], limits=limits)
    if require_nonzero:
        native = solve_nonempty(prepared['vertices'], prepared['edges'], prepared['label_rows'],
                                max_pin_cases=max_pin_cases, **arguments)
    else:
        native = solve_tjoin(prepared['vertices'], prepared['edges'], prepared['label_rows'], **arguments)
    result = {'schema': 'certified_graph_lift_code_v1', 'n': n, 'dimension': prepared['dimension'],
              'target': target, 'require_nonzero': require_nonzero,
              'row_transform': list(prepared['row_transform']), 'graph_rows': graph_rows,
              'transformed_rows': list(prepared['rows']), 'transformed_target': prepared['transformed_target'],
              'weights': list(prepared['weights']), 'native': native, 'status': native['status'],
              'distance': native['weight'],
              'upper_bound': native.get('upper_bound', native['weight']), 'word': native['word'],
              'solve_seconds': perf_counter() - started}
    # Producer nested certificates have already been checked under their declared
    # limits. The public independent verifier is deliberately a separate entry point.
    if result['word'] is not None:
        word = result['word']
        actual_target = sum(((row & word).bit_count() % 2) << i for i, row in enumerate(prepared['original_rows']))
        actual_weight = sum(w for j, w in enumerate(prepared['weights']) if word >> j & 1)
        if actual_target != target or actual_weight != result['upper_bound'] or (require_nonzero and not word):
            raise ArithmeticError('native reconstruction fails the original code request')
    return result


def verify_code(check_rows, n, result, *, target=0, require_nonzero=True, weights=None,
                **verification_limits):
    try:
        if not isinstance(result, dict) or result.get('schema') != 'certified_graph_lift_code_v1':
            raise ValueError('invalid code certificate schema')
        prepared = prepare_code(check_rows, n, result['graph_rows'], row_transform=result['row_transform'],
                                target=target, require_nonzero=require_nonzero, weights=weights)
        scalar = {'n': n, 'dimension': prepared['dimension'], 'target': target,
                  'transformed_target': prepared['transformed_target']}
        for name, expected in scalar.items():
            if type(result.get(name)) is not int or result[name] != expected:
                raise ValueError('code metadata does not match the requested problem')
        if type(result.get('require_nonzero')) is not bool or result['require_nonzero'] != require_nonzero:
            raise ValueError('nonzero condition mismatch')
        for name, expected in (('transformed_rows', prepared['rows']), ('weights', prepared['weights'])):
            given = result.get(name)
            if not isinstance(given, list) or any(type(v) is not int for v in given) or given != list(expected):
                raise ValueError('normal-form rows or objective weights mismatch')
        native = result['native']
        verify = verify_nonempty if require_nonzero else verify_tjoin
        checked = verify(prepared['vertices'], prepared['edges'], prepared['label_rows'], native,
                         terminals=prepared['terminals'], target=prepared['label_target'], **verification_limits)
        if not checked['valid']:
            if checked['status'] == 'UNKNOWN':
                return checked
            raise ValueError('labelled-join certificate rejected: ' + '; '.join(checked['errors']))
        expected = {'status': native['status'], 'distance': native['weight'],
                    'upper_bound': native.get('upper_bound', native['weight']), 'word': native['word']}
        for name, value in expected.items():
            if result.get(name) != value or (name != 'status' and value is not None and type(result[name]) is not int):
                raise ValueError('code aggregate result mismatch')
        word = result['word']
        if word is not None:
            if type(word) is not int or word < 0 or word.bit_length() > n or (require_nonzero and not word):
                raise ValueError('invalid original-coordinate witness')
            rhs = sum(((row & word).bit_count() % 2) << i for i, row in enumerate(prepared['original_rows']))
            weight = sum(w for j, w in enumerate(prepared['weights']) if word >> j & 1)
            if rhs != target or weight != result['upper_bound']:
                raise ValueError('original equations or weight fail')
        return {'valid': True, 'status': result['status'], 'errors': [],
                'distance': result['distance'], 'upper_bound': result['upper_bound'],
                'graph_rows': prepared['graph_rows'], 'label_rows': prepared['label_rows']}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {'valid': False, 'status': 'INVALID', 'errors': [str(exc)]}
