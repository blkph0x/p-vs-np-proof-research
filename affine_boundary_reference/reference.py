"""Independent block-support / quadratic-pair boundary reference.

No import from the one-bit boundary implementation. Original coordinate IDs
are retained. Certificates verify support projection by a left-nullspace,
then a bijective internal parametrization and pair identities.
"""
from fractions import Fraction
from hashlib import sha256

DEFAULTS = dict(max_variables=4096, max_rows=16384, max_terms=100000,
                max_work=4000000, max_scalar_bits=65536, max_steps=4096)


class Exhausted(Exception):
    pass


class Meter:
    def __init__(self, caps):
        if set(caps)-set(DEFAULTS):
            raise ValueError('unknown cap')
        self.caps = {**DEFAULTS, **caps}
        if any(type(v) is not int or v < 0 for v in self.caps.values()):
            raise ValueError('caps must be nonnegative exact integers')
        self.work = 0
        self.peak_terms = 0
        self.scalar_bits = 0

    def tick(self, count=1):
        self.work += count
        if self.work > self.caps['max_work']:
            raise Exhausted('work cap')

    def terms(self, p):
        self.peak_terms = max(self.peak_terms, len(p))
        if len(p) > self.caps['max_terms']:
            raise Exhausted('phase term cap')
        return p

    def scalar(self, x):
        self.scalar_bits = max(self.scalar_bits, abs(x.numerator).bit_length(), x.denominator.bit_length())
        if self.scalar_bits > self.caps['max_scalar_bits']:
            raise Exhausted('scalar bit cap')
        return x

    def stats(self):
        return dict(work=self.work, peak_terms=self.peak_terms, scalar_bits=self.scalar_bits)


def rational(x):
    if type(x) in (int, Fraction):
        return Fraction(x)
    if type(x) in (list, tuple) and len(x) == 2 and all(type(v) is int for v in x) and x[1] > 0:
        return Fraction(*x)
    raise ValueError('invalid exact rational')


def pair(x):
    return [x.numerator, x.denominator]


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


def toggle(p, term):
    if term in p:
        p.remove(term)
    else:
        p.add(term)


def _ids(ids, n, label):
    if type(ids) not in (list, tuple) or any(type(v) is not int or not 0 <= v < n for v in ids) or len(set(ids)) != len(ids):
        raise ValueError('invalid '+label)
    return list(ids)


def _algebra(n, allowed, equations, phase, scalar, meter):
    allowed_mask = sum(1 << v for v in allowed)
    if type(equations) not in (list, tuple) or type(phase) not in (list, tuple, set):
        raise ValueError('equations and phase must be explicit collections')
    if len(equations) > meter.caps['max_rows'] or len(phase) > meter.caps['max_terms']:
        raise Exhausted('input row or term cap')
    rows = []
    for row in equations:
        if type(row) not in (list, tuple) or len(row) != 2 or any(type(v) is not int for v in row) or row[0] < 0 or row[0] & ~allowed_mask or row[1] not in (0, 1):
            raise ValueError('invalid or inactive support coordinate')
        rows.append(list(row))
    polynomial = set()
    for term in phase:
        if type(term) is not int or term < 0 or term & ~allowed_mask or term.bit_count() > 2:
            raise ValueError('invalid or inactive quadratic term')
        toggle(polynomial, term)
    meter.tick(len(rows)+len(phase))
    return rows, polynomial, meter.scalar(rational(scalar))


def _request(n, retained, equations, phase, scalar, active, meter):
    if type(n) is not int or n < 0:
        raise ValueError('invalid coordinate dimension')
    if n > meter.caps['max_variables']:
        raise Exhausted('coordinate cap')
    retained = _ids(retained, n, 'retained IDs')
    active = list(range(n)) if active is None else _ids(active, n, 'active IDs')
    if not set(retained) <= set(active):
        raise ValueError('retained ID is inactive')
    internal = [v for v in active if v not in set(retained)]
    if len(internal) > meter.caps['max_steps']:
        raise Exhausted('internal-coordinate cap')
    rows, polynomial, scalar = _algebra(n, active, equations, phase, scalar, meter)
    return retained, active, internal, rows, polynomial, scalar


def _hash(n, retained, active, rows, polynomial, scalar):
    digest = sha256(b'block-affine-boundary-v1')
    def integer(v):
        digest.update(bytes([v < 0]))
        raw = abs(v).to_bytes(max(1, (abs(v).bit_length()+7)//8), 'little')
        digest.update(len(raw).to_bytes(8, 'little'))
        digest.update(raw)
    integer(n)
    for seq in (retained, active):
        integer(len(seq))
        for v in seq:
            integer(v)
    integer(len(rows))
    for mask, rhs in rows:
        integer(mask); integer(rhs)
    integer(len(polynomial))
    for term in sorted(polynomial):
        integer(term)
    integer(scalar.numerator); integer(scalar.denominator)
    return digest.hexdigest()


def _rref(equations, columns, meter):
    rows = [list(row) for row in equations]
    pivots, rank = [], 0
    for v in columns:
        selected = None
        for j in range(rank, len(rows)):
            meter.tick()
            if rows[j][0] >> v & 1:
                selected = j
                break
        if selected is None:
            continue
        rows[rank], rows[selected] = rows[selected], rows[rank]
        for j in range(len(rows)):
            meter.tick()
            if j != rank and rows[j][0] >> v & 1:
                rows[j][0] ^= rows[rank][0]
                rows[j][1] ^= rows[rank][1]
        pivots.append(v)
        rank += 1
    return rows, pivots


def _support(equations, retained, meter):
    rows, pivots = _rref(equations, retained, meter)
    if any(mask == 0 and rhs for mask, rhs in rows):
        return None
    rows = rows[:len(pivots)]
    free = [v for v in retained if v not in set(pivots)]
    expressions = {v: (1 << v, 0) for v in free}
    for (mask, rhs), v in zip(rows, pivots):
        expressions[v] = (mask ^ (1 << v), rhs)
    return rows, pivots, free, expressions


def _affine_terms(expression):
    mask, constant = expression
    return {1 << v for v in bits(mask)} | ({0} if constant else set())


def _multiply(a, b, meter):
    out = set()
    for x in a:
        for y in b:
            toggle(out, x | y)
            meter.tick()
    return meter.terms(out)


def _substitute(polynomial, expressions, meter):
    result = set()
    for term in polynomial:
        variables = list(bits(term))
        if not variables:
            toggle(result, 0)
        elif len(variables) == 1:
            result ^= _affine_terms(expressions[variables[0]])
        else:
            result ^= _multiply(_affine_terms(expressions[variables[0]]),
                                _affine_terms(expressions[variables[1]]), meter)
        meter.tick()
        meter.terms(result)
    return result


def _zero(n, retained):
    return dict(n=n, retained=list(retained), zero=True, equations=[], phase=[], scalar=[0, 1], free_ids=[])


def _message(n, retained, equations, polynomial, scalar, meter):
    if not scalar:
        return _zero(n, retained)
    support = _support(equations, retained, meter)
    if support is None:
        return _zero(n, retained)
    rows, pivots, free, expressions = support
    reduced = _substitute(polynomial, expressions, meter)
    if 0 in reduced:
        scalar = -scalar
        reduced.remove(0)
    return dict(n=n, retained=list(retained), zero=False, equations=rows,
                phase=sorted(reduced), scalar=pair(meter.scalar(scalar)), free_ids=free)


def _project_support_by_left_kernel(rows, retained, internal, meter):
    """Independent of producer elimination: ker(A_z^T) gives all conditions."""
    transposed = []
    for v in internal:
        mask = sum(((row[0] >> v) & 1) << i for i, row in enumerate(rows))
        transposed.append([mask, 0])
        meter.tick(len(rows))
    reduced, pivots = _rref(transposed, list(range(len(rows))), meter)
    free = [j for j in range(len(rows)) if j not in set(pivots)]
    conditions = []
    for j in free:
        combination = 1 << j
        for i, v in enumerate(pivots):
            if reduced[i][0] >> j & 1:
                combination |= 1 << v
            meter.tick()
        mask, rhs = 0, 0
        for i in bits(combination):
            mask ^= rows[i][0]
            rhs ^= rows[i][1]
            meter.tick()
        conditions.append([mask, rhs])
    return _support(conditions, retained, meter), len(pivots)


def _parametrize(n, active, retained, internal, rows, meter):
    reduced, pivots = _rref(rows, internal, meter)
    support = _support(reduced[len(pivots):], retained, meter)
    if support is None:
        return None
    free = [v for v in internal if v not in set(pivots)]
    expressions = {v: (1 << v, 0) for v in retained}
    for i, v in enumerate(free):
        expressions[v] = (1 << (n+i), 0)
    for i, v in enumerate(pivots):
        mask, rhs = reduced[i]
        result = 0
        for other in bits(mask ^ (1 << v)):
            result ^= expressions[other][0]
        expressions[v] = (result, rhs)
    return dict(boundary_equations=support[0], free_internal=free,
                expressions=[[v, *expressions[v]] for v in active])


def _check_param(n, active, retained, internal, rows, parameter, meter):
    expected, rank = _project_support_by_left_kernel(rows, retained, internal, meter)
    if expected is None:
        return False
    if type(parameter) is not dict or set(parameter) != {'boundary_equations', 'free_internal', 'expressions'}:
        return False
    drows, _, _ = _algebra(n, retained, parameter['boundary_equations'], [], 1, meter)
    actual = _support(drows, retained, meter)
    if actual is None or actual[0] != expected[0]:
        return False
    free = _ids(parameter['free_internal'], n, 'free internal IDs')
    if not set(free) <= set(internal) or len(free) != len(internal)-rank:
        return False
    raw = parameter['expressions']
    if type(raw) is not list or len(raw) != len(active):
        return False
    allowed = sum(1 << v for v in retained) | (((1 << len(free))-1) << n)
    expressions = {}
    for item, v in zip(raw, active):
        if type(item) is not list or len(item) != 3 or any(type(x) is not int for x in item) or item[0] != v or item[1] < 0 or item[1] & ~allowed or item[2] not in (0, 1):
            return False
        expressions[v] = (item[1], item[2])
    if any(expressions[v] != (1 << v, 0) for v in retained) or any(expressions[v] != (1 << (n+i), 0) for i, v in enumerate(free)):
        return False
    # Each original free coordinate is its own parameter: injectivity is explicit.
    # The checked nullity then proves every internal solution is covered.
    for mask, rhs in rows:
        residual, constant = 0, rhs
        for v in bits(mask):
            residual ^= expressions[v][0]
            constant ^= expressions[v][1]
            meter.tick()
        if residual >> n:
            return False
        reduced = _substitute({1 << v for v in bits(residual)} | ({0} if constant else set()), expected[3], meter)
        if reduced:
            return False
    return True


def _eliminate_pairs(n, retained, parameter, polynomial, scalar, meter):
    expressions = {v: (mask, constant) for v, mask, constant in parameter['expressions']}
    reduced = _substitute(polynomial, expressions, meter)
    initial = sorted(reduced)
    internal = list(range(n, n+len(parameter['free_internal'])))
    active = set(internal)
    trace = []
    factor_power = 0
    while True:
        meter.tick(len(reduced))
        pair_term = next((term for term in sorted(reduced) if term.bit_count() == 2 and all(v in active for v in bits(term))), None)
        if pair_term is None:
            break
        i, j = list(bits(pair_term))
        a = {term ^ (1 << i) for term in reduced if term != pair_term and term >> i & 1}
        b = {term ^ (1 << j) for term in reduced if term != pair_term and term >> j & 1}
        reduced = {term for term in reduced if not term & pair_term} ^ _multiply(a, b, meter)
        meter.terms(reduced)
        active -= {i, j}
        trace.append({'pair': [i, j], 'after': sorted(reduced)})
        factor_power += 1
    boundary_mask = sum(1 << v for v in retained)
    final_phase = {term for term in reduced if not term & ~boundary_mask}
    equations = [list(row) for row in parameter['boundary_equations']]
    for i in sorted(active):
        coefficient = {term ^ (1 << i) for term in reduced if term >> i & 1}
        if any(term.bit_count() > 1 or term & ~boundary_mask for term in coefficient):
            raise ArithmeticError('residual internal cross term')
        equations.append([sum(term for term in coefficient if term), int(0 in coefficient)])
        factor_power += 1
    if len(equations) > meter.caps['max_rows']:
        raise Exhausted('derived boundary row cap')
    value = meter.scalar(scalar * (1 << factor_power))
    message = _message(n, retained, equations, final_phase, value, meter)
    return message, dict(initial_phase=initial, pairs=trace, factor_power=factor_power)


def marginalize_reference(n, retained, equations, phase, scalar=1, *, active=None, **caps):
    meter = Meter(caps)
    try:
        retained, active, internal, rows, polynomial, scalar = _request(n, retained, equations, phase, scalar, active, meter)
        digest = _hash(n, retained, active, rows, polynomial, scalar)
        if not scalar:
            certificate = dict(kind='zero-scalar', input_sha256=digest)
            message = _zero(n, retained)
        else:
            parameter = _parametrize(n, active, retained, internal, rows, meter)
            if parameter is None:
                certificate = dict(kind='inconsistent-support', input_sha256=digest)
                message = _zero(n, retained)
            else:
                message, trace = _eliminate_pairs(n, retained, parameter, polynomial, scalar, meter)
                certificate = dict(kind='block-pair', input_sha256=digest, parameter=parameter, **trace)
        return dict(status='EXACT', message=message, certificate=certificate, stats=meter.stats())
    except Exhausted as e:
        return dict(status='UNKNOWN', message=None, certificate=None, reason=str(e), stats=meter.stats())


def _parse_message(n, retained, message, meter):
    fields = {'n', 'retained', 'zero', 'equations', 'phase', 'scalar', 'free_ids'}
    if type(message) is not dict or set(message) != fields or type(message['n']) is not int or message['n'] != n or _ids(message['retained'], n, 'message boundary') != retained or type(message['zero']) is not bool:
        raise ValueError('invalid message or ordered boundary')
    if message['zero']:
        if message != _zero(n, retained) or any(type(v) is not int for v in message['scalar']):
            raise ValueError('noncanonical zero message')
        return None
    rows, phase, scalar = _algebra(n, retained, message['equations'], message['phase'], message['scalar'], meter)
    support = _support(rows, retained, meter)
    if not scalar or support is None or _ids(message['free_ids'], n, 'free boundary IDs') != support[2]:
        raise ValueError('invalid nonzero support or free coordinate metadata')
    return support, phase, scalar


def _equivalent(n, retained, left, right, meter):
    a, b = _parse_message(n, retained, left, meter), _parse_message(n, retained, right, meter)
    if a is None or b is None:
        return a is None and b is None, 'zero support'
    if a[0][0] != b[0][0]:
        return False, 'different affine supports'
    if a[2] not in (b[2], -b[2]):
        return False, 'different nonzero magnitudes'
    difference = _substitute(a[1] ^ b[1], a[0][3], meter)
    expected = set() if a[2] == b[2] else {0}
    return difference == expected, 'phase equality on the common affine support'


def equivalent_messages(n, retained, left, right, **caps):
    meter = Meter(caps)
    try:
        if type(n) is not int or n < 0:
            raise ValueError('invalid dimension')
        if n > meter.caps['max_variables']:
            raise Exhausted('coordinate cap')
        retained = _ids(retained, n, 'retained IDs')
        equal, reason = _equivalent(n, retained, left, right, meter)
        return dict(status='EXACT', equivalent=equal, reason=reason, stats=meter.stats())
    except Exhausted as e:
        return dict(status='UNKNOWN', equivalent=None, reason=str(e), stats=meter.stats())
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as e:
        return dict(status='INVALID', equivalent=None, reason=str(e), stats=meter.stats())


def verify_reference(n, retained, equations, phase, scalar, result, *, active=None, **caps):
    meter = Meter(caps)
    try:
        retained, active, internal, rows, polynomial, scalar = _request(n, retained, equations, phase, scalar, active, meter)
        if type(result) is not dict or result.get('status') != 'EXACT' or type(result.get('certificate')) is not dict:
            raise ValueError('expected EXACT reference result')
        cert = result['certificate']
        if cert.get('input_sha256') != _hash(n, retained, active, rows, polynomial, scalar):
            raise ValueError('external input mismatch')
        kind = cert.get('kind')
        if kind == 'zero-scalar':
            if set(cert) != {'kind', 'input_sha256'} or scalar:
                raise ValueError('false zero scalar')
            expected = _zero(n, retained)
        elif kind == 'inconsistent-support':
            if set(cert) != {'kind', 'input_sha256'} or _project_support_by_left_kernel(rows, retained, internal, meter)[0] is not None:
                raise ValueError('false inconsistent support')
            expected = _zero(n, retained)
        else:
            fields = {'kind', 'input_sha256', 'parameter', 'initial_phase', 'pairs', 'factor_power'}
            if set(cert) != fields or kind != 'block-pair' or not scalar or not _check_param(n, active, retained, internal, rows, cert['parameter'], meter):
                raise ValueError('invalid block parametrization')
            parameter = cert['parameter']
            expressions = {v: (mask, constant) for v, mask, constant in parameter['expressions']}
            reduced = _substitute(polynomial, expressions, meter)
            if type(cert['initial_phase']) is not list or any(type(v) is not int for v in cert['initial_phase']) or cert['initial_phase'] != sorted(reduced) or type(cert['pairs']) is not list:
                raise ValueError('invalid initial restricted phase')
            active_t = set(range(n, n+len(parameter['free_internal'])))
            power = 0
            for step in cert['pairs']:
                if type(step) is not dict or set(step) != {'pair', 'after'} or type(step['pair']) is not list or len(step['pair']) != 2:
                    raise ValueError('malformed pair step')
                i, j = step['pair']
                if type(i) is not int or type(j) is not int or i == j or i not in active_t or j not in active_t:
                    raise ValueError('invalid active internal pair')
                pair_term = (1 << i) | (1 << j)
                if pair_term not in reduced:
                    raise ValueError('absent quadratic pair')
                left, right, rest = set(), set(), set()
                for term in reduced:
                    if term == pair_term:
                        continue
                    if term & (1 << i):
                        left.add(term & ~(1 << i))
                    elif term & (1 << j):
                        right.add(term & ~(1 << j))
                    else:
                        rest.add(term)
                    meter.tick()
                for a in left:
                    for b in right:
                        toggle(rest, a | b)
                        meter.tick()
                if type(step['after']) is not list or any(type(v) is not int for v in step['after']) or step['after'] != sorted(rest):
                    raise ValueError('invalid pair elimination identity')
                reduced = meter.terms(rest)
                active_t -= {i, j}
                power += 1
            boundary_mask = sum(1 << v for v in retained)
            if any(term.bit_count() == 2 and all(v in active_t for v in bits(term)) for term in reduced):
                raise ValueError('uneliminated internal quadratic pair')
            equations_out = [list(row) for row in parameter['boundary_equations']]
            phase_out = set()
            coefficients = {v: [0, 0] for v in active_t}
            for term in reduced:
                internal_part = term & ~boundary_mask
                if not internal_part:
                    toggle(phase_out, term)
                else:
                    ids = list(bits(internal_part))
                    if len(ids) != 1 or ids[0] not in active_t:
                        raise ValueError('invalid remaining internal term')
                    remainder = term ^ internal_part
                    if remainder:
                        coefficients[ids[0]][0] ^= remainder
                    else:
                        coefficients[ids[0]][1] ^= 1
                meter.tick()
            for v in sorted(active_t):
                equations_out.append(coefficients[v])
                power += 1
            if type(cert['factor_power']) is not int or cert['factor_power'] != power:
                raise ValueError('wrong summation multiplicity')
            if len(equations_out) > meter.caps['max_rows']:
                raise Exhausted('derived boundary row cap')
            expected = _message(n, retained, equations_out, phase_out, meter.scalar(scalar*(1 << power)), meter)
        equal, _ = _equivalent(n, retained, expected, result.get('message'), meter)
        if not equal:
            raise ValueError('reported boundary function differs')
        return dict(valid=True, status='VERIFIED', stats=meter.stats())
    except Exhausted as e:
        return dict(valid=False, status='UNKNOWN', reason=str(e), stats=meter.stats())
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as e:
        return dict(valid=False, status='INVALID', reason=str(e), stats=meter.stats())
