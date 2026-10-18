"""Compact exact marginalization of rational real-affine Boolean functions.

Masks always use the original n positions. Only active variables are part of
the function, and only active minus retained variables are summed. No truth
table is built. The verifier replays one-bit identities using separate row
reduction and polynomial substitution implementations.
"""
from fractions import Fraction
from hashlib import sha256


LIMITS = dict(max_variables=4096, max_rows=16384, max_terms=100000,
              max_work=4000000, max_scalar_bits=65536, max_steps=4096)


class Exhausted(Exception):
    pass


class Budget:
    def __init__(self, overrides):
        if set(overrides) - set(LIMITS):
            raise ValueError('unknown budget')
        self.limits = {**LIMITS, **overrides}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError('budgets must be nonnegative exact integers')
        self.work = self.peak_rows = self.peak_terms = self.peak_scalar_bits = 0
        self.steps = self.hash_bytes = 0

    def tick(self, count=1):
        self.work += count
        if self.work > self.limits['max_work']:
            raise Exhausted('work budget')

    def state(self, rows, phase):
        self.peak_rows = max(self.peak_rows, len(rows))
        self.peak_terms = max(self.peak_terms, len(phase))
        if len(rows) > self.limits['max_rows']:
            raise Exhausted('support row budget')
        if len(phase) > self.limits['max_terms']:
            raise Exhausted('phase term budget')

    def scalar(self, x):
        bits = max(abs(x.numerator).bit_length(), x.denominator.bit_length())
        self.peak_scalar_bits = max(self.peak_scalar_bits, bits)
        if bits > self.limits['max_scalar_bits']:
            raise Exhausted('scalar bit budget')
        return x

    def stats(self):
        return dict(work=self.work, steps=self.steps, peak_rows=self.peak_rows,
                    peak_terms=self.peak_terms, peak_scalar_bits=self.peak_scalar_bits,
                    hash_bytes=self.hash_bytes)


def ratio(value):
    if type(value) in (int, Fraction):
        return Fraction(value)
    if type(value) in (list, tuple) and len(value) == 2:
        numerator, denominator = value
        if type(numerator) is int and type(denominator) is int and denominator > 0:
            return Fraction(numerator, denominator)
    raise ValueError('scalar must be an exact rational, excluding booleans')


def pack(value):
    return [value.numerator, value.denominator]


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit
        mask ^= bit


def _toggle(poly, term):
    if term in poly:
        poly.remove(term)
    else:
        poly.add(term)


def _ids(values, n, name):
    if type(values) not in (list, tuple) or any(type(i) is not int or not 0 <= i < n for i in values):
        raise ValueError(name + ' must contain original coordinate IDs')
    if len(set(values)) != len(values):
        raise ValueError(name + ' contains duplicate IDs')
    return list(values)


def _request(n, retained, equations, phase, scalar, active, order, budget):
    if type(n) is not int or n < 0:
        raise ValueError('n must be a nonnegative exact integer')
    # Guard binary-encoded giant dimensions before range allocation or shifts.
    if n > budget.limits['max_variables']:
        raise Exhausted('coordinate dimension budget')
    active = list(range(n)) if active is None else _ids(active, n, 'active')
    retained = _ids(retained, n, 'retained')
    if not set(retained) <= set(active):
        raise ValueError('retained must be a subset of active')
    internal = set(active) - set(retained)
    order = sorted(internal) if order is None else _ids(order, n, 'order')
    if set(order) != internal:
        raise ValueError('order must eliminate each active internal ID exactly once')
    if len(order) > budget.limits['max_steps']:
        raise Exhausted('elimination step budget')
    active_mask = sum(1 << i for i in active)
    if type(equations) not in (list, tuple) or type(phase) not in (list, tuple, set):
        raise ValueError('equations and phase must be explicit collections')
    budget.state(equations, phase)
    rows = []
    for row in equations:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('support rows are (mask, rhs) pairs')
        mask, rhs = row
        if type(mask) is not int or mask < 0 or mask.bit_length() > n or mask & ~active_mask:
            raise ValueError('support mask uses an invalid or inactive coordinate')
        if type(rhs) is not int or rhs not in (0, 1):
            raise ValueError('support rhs must be exact zero or one')
        rows.append((mask, rhs))
        budget.tick()
    poly = set()
    for term in phase:
        if type(term) is not int or term < 0 or term.bit_length() > n or term & ~active_mask or term.bit_count() > 2:
            raise ValueError('phase terms must have degree at most two on active IDs')
        _toggle(poly, term)
        budget.tick()
    value = budget.scalar(ratio(scalar))
    budget.tick(len(active) + len(retained) + len(order) + 1)
    return n, retained, rows, poly, value, active, order


def _digest(request, budget):
    n, retained, rows, poly, scalar, active, order = request
    h = sha256(b'compact-real-affine-boundary-v1')
    def integer(x):
        data = abs(x).to_bytes(max(1, (abs(x).bit_length() + 7)//8), 'little')
        h.update(bytes([x < 0]))
        h.update(len(data).to_bytes(8, 'little'))
        h.update(data)
        budget.hash_bytes += 9 + len(data)
    integer(n)
    for values in (retained, active, order):
        integer(len(values))
        for x in values:
            integer(x)
    integer(len(rows))
    for mask, rhs in rows:
        integer(mask); integer(rhs)
    integer(len(poly))
    for term in sorted(poly):
        integer(term)
    integer(scalar.numerator); integer(scalar.denominator)
    return h.hexdigest()


def _substitute_bit(poly, bit, mask, rhs, budget):
    affine = list(_bits(mask)) + ([0] if rhs else [])
    out = set()
    for term in poly:
        if not term & bit:
            _toggle(out, term)
            budget.tick()
        else:
            other = term ^ bit
            for replacement in affine:
                _toggle(out, other | replacement)
                budget.tick()
        budget.state((), out)
    return out


def _producer_step(rows, poly, scalar, variable, budget):
    bit = 1 << variable
    pivot = next((i for i, (mask, rhs) in enumerate(rows) if mask & bit), None)
    budget.tick(len(rows))
    if pivot is not None:
        mask, rhs = rows[pivot]
        reduced = []
        for i, (a, b) in enumerate(rows):
            if i != pivot:
                reduced.append((a ^ mask, b ^ rhs) if a & bit else (a, b))
            budget.tick()
        poly = _substitute_bit(poly, bit, mask ^ bit, rhs, budget)
        step = dict(variable=variable, kind='pivot', row=pivot)
        rows = reduced
    else:
        coefficient, constant, out = 0, 0, set()
        for term in poly:
            if term & bit:
                residual = term ^ bit
                if residual:
                    coefficient ^= residual
                else:
                    constant ^= 1
            else:
                out.add(term)
            budget.tick()
        rows = rows + [(coefficient, constant)]
        poly = out
        scalar = budget.scalar(scalar * 2)
        step = dict(variable=variable, kind='free')
    budget.steps += 1
    budget.state(rows, poly)
    return rows, poly, scalar, step


def _rref(rows, retained, budget):
    rows = [list(row) for row in rows]
    rank = 0
    pivots = []
    for variable in retained:
        bit = 1 << variable
        selected = next((i for i in range(rank, len(rows)) if rows[i][0] & bit), None)
        budget.tick(1 + len(rows) - rank)
        if selected is None:
            continue
        rows[rank], rows[selected] = rows[selected], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][0] & bit:
                rows[i][0] ^= rows[rank][0]
                rows[i][1] ^= rows[rank][1]
            budget.tick()
        pivots.append(variable)
        rank += 1
    if any(mask == 0 and rhs for mask, rhs in rows):
        return None, None
    return rows[:rank], pivots


def _zero(n, retained):
    return dict(n=n, retained=list(retained), zero=True, equations=[], phase=[],
                scalar=[0, 1], free_ids=[])


def _normalize(n, retained, rows, poly, scalar, budget):
    if not scalar:
        return _zero(n, retained)
    reduced, pivots = _rref(rows, retained, budget)
    if reduced is None:
        return _zero(n, retained)
    for variable, (mask, rhs) in zip(pivots, reduced):
        poly = _substitute_bit(poly, 1 << variable, mask ^ (1 << variable), rhs, budget)
    if 0 in poly:
        poly.remove(0)
        scalar = -scalar
    return dict(n=n, retained=list(retained), zero=False, equations=reduced,
                phase=sorted(poly), scalar=pack(scalar),
                free_ids=[i for i in retained if i not in pivots])


def message_key(message):
    """Scalar-independent immutable key of an already canonical message.

    This helper is not a certificate checker. Use verified/produced messages.
    Original coordinate dimension and retained order are deliberately included.
    """
    return (message['n'], tuple(message['retained']), message['zero'],
            tuple(tuple(row) for row in message['equations']), tuple(message['phase']))


def marginalize(n, retained, equations, phase, scalar=1, *, active=None, order=None, **caps):
    budget = Budget(caps)
    try:
        request = _request(n, retained, equations, phase, scalar, active, order, budget)
        digest = _digest(request, budget)
        n, retained, rows, poly, scalar, active, order = request
        trace = []
        for variable in order:
            rows, poly, scalar, step = _producer_step(rows, poly, scalar, variable, budget)
            trace.append(step)
        message = _normalize(n, retained, rows, poly, scalar, budget)
        certificate = dict(kind='one-bit-affine-marginal-v1', input_sha256=digest, steps=trace)
        return dict(status='EXACT', message=message, certificate=certificate,
                    key=message_key(message), stats=budget.stats())
    except Exhausted as exc:
        return dict(status='UNKNOWN', message=None, certificate=None, key=None,
                    reason=str(exc), stats=budget.stats())


def normalize_message(n, retained, equations, phase, scalar=1, **caps):
    """Canonicalize a function of exactly retained IDs, without summing bits."""
    return marginalize(n, retained, equations, phase, scalar, active=retained, order=[], **caps)


def _checker_substitute(poly, replacements, budget):
    """Expand each degree-two monomial using generic polynomial products."""
    output = set()
    for term in poly:
        expression = {0}
        for bit in _bits(term):
            factor = replacements.get(bit, {bit})
            product = set()
            for a in expression:
                for b in factor:
                    _toggle(product, a | b)
                    budget.tick()
            expression = product
            budget.state((), expression)
        for item in expression:
            _toggle(output, item)
            budget.tick()
        budget.state((), output)
    return output


def _checker_step(rows, poly, scalar, variable, step, budget):
    if type(step) is not dict or type(step.get('variable')) is not int or step['variable'] != variable:
        raise ValueError('wrong or malformed eliminated variable')
    bit = 1 << variable
    if step.get('kind') == 'pivot':
        if set(step) != {'variable', 'kind', 'row'} or type(step['row']) is not int or not 0 <= step['row'] < len(rows):
            raise ValueError('invalid pivot row')
        index = step['row']
        pivot_mask, pivot_rhs = rows[index]
        if not pivot_mask & bit:
            raise ValueError('chosen support row does not contain the eliminated variable')
        rows = list(rows)
        del rows[index]
        for j in range(len(rows)):
            if rows[j][0] & bit:
                rows[j] = (rows[j][0] ^ pivot_mask, rows[j][1] ^ pivot_rhs)
            budget.tick()
        expression = set(_bits(pivot_mask ^ bit))
        if pivot_rhs:
            expression.add(0)
        poly = _checker_substitute(poly, {bit: expression}, budget)
    elif step.get('kind') == 'free':
        if set(step) != {'variable', 'kind'}:
            raise ValueError('malformed free step')
        for mask, rhs in rows:
            budget.tick()
            if mask & bit:
                raise ValueError('claimed free variable occurs in support')
        coefficient = set()
        remaining = set()
        for monomial in poly:
            if monomial & bit:
                coefficient.add(monomial ^ bit)
            else:
                remaining.add(monomial)
            budget.tick()
        mask = sum(term for term in coefficient if term)
        rows = list(rows) + [(mask, int(0 in coefficient))]
        poly = remaining
        scalar = budget.scalar(scalar * 2)
    else:
        raise ValueError('unknown elimination rule')
    budget.steps += 1
    budget.state(rows, poly)
    return rows, poly, scalar


def _checker_normalize(n, retained, rows, poly, scalar, budget):
    if not scalar:
        return _zero(n, retained)
    basis = {}
    for mask, rhs in rows:
        for variable in retained:
            budget.tick()
            bit = 1 << variable
            if mask & bit and variable in basis:
                old_mask, old_rhs = basis[variable]
                mask ^= old_mask
                rhs ^= old_rhs
        if not mask:
            if rhs:
                return _zero(n, retained)
            continue
        variable = next(i for i in retained if mask & (1 << i))
        bit = 1 << variable
        for other in basis:
            old_mask, old_rhs = basis[other]
            if old_mask & bit:
                basis[other] = (old_mask ^ mask, old_rhs ^ rhs)
            budget.tick()
        basis[variable] = (mask, rhs)
    reduced = [list(basis[i]) for i in retained if i in basis]
    replacements = {}
    for variable, (mask, rhs) in basis.items():
        expression = set(_bits(mask ^ (1 << variable)))
        if rhs:
            expression.add(0)
        replacements[1 << variable] = expression
    poly = _checker_substitute(poly, replacements, budget)
    if 0 in poly:
        poly.remove(0)
        scalar = -scalar
    return dict(n=n, retained=list(retained), zero=False, equations=reduced,
                phase=sorted(poly), scalar=pack(scalar),
                free_ids=[i for i in retained if i not in basis])


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(_same(left[key], right[key]) for key in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def verify_marginal(n, retained, equations, phase, scalar, result, *, active=None, order=None, **caps):
    budget = Budget(caps)
    try:
        request = _request(n, retained, equations, phase, scalar, active, order, budget)
        digest = _digest(request, budget)
        n, retained, rows, poly, scalar, active, order = request
        if type(result) is not dict or result.get('status') != 'EXACT' or type(result.get('certificate')) is not dict:
            raise ValueError('expected an EXACT marginal certificate')
        certificate = result['certificate']
        if set(certificate) != {'kind', 'input_sha256', 'steps'} or certificate['kind'] != 'one-bit-affine-marginal-v1' or certificate['input_sha256'] != digest:
            raise ValueError('external original input mismatch')
        trace = certificate['steps']
        if type(trace) is not list or len(trace) != len(order):
            raise ValueError('every active internal variable must be eliminated exactly once')
        for variable, step in zip(order, trace):
            rows, poly, scalar = _checker_step(rows, poly, scalar, variable, step, budget)
        expected = _checker_normalize(n, retained, rows, poly, scalar, budget)
        if not _same(result.get('message'), expected):
            raise ValueError('incorrect canonical marginal')
        # JSON turns tuple keys into lists. Keys and producer statistics are
        # conveniences, not trusted certificate fields; derive the key afresh.
        return dict(valid=True, status='VERIFIED', errors=[], message=expected,
                    key=message_key(expected), stats=budget.stats())
    except Exhausted as exc:
        return dict(valid=False, status='UNKNOWN', errors=[str(exc)], stats=budget.stats())
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, AttributeError) as exc:
        return dict(valid=False, status='INVALID', errors=[str(exc)], stats=budget.stats())


verify = verify_marginal
