"""Bounded exact rational-basis / real-affine Holant evaluator.

Tables are LSB-first. Every edge occurs once in each bipartite side.
The verifier checks explicit local decompositions and global algebra; it
does not invoke recognition or the producer's Gauss-sum reduction.
"""
from fractions import Fraction
from hashlib import sha256
from math import comb


LIMITS = dict(max_edges=512, max_entries=100000, max_work=3000000,
              max_integer_bits=100000)


class Exhausted(Exception):
    pass


class Budget:
    def __init__(self, overrides):
        if set(overrides) - set(LIMITS):
            raise ValueError("unknown budget")
        self.limits = {**LIMITS, **overrides}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError("caps must be nonnegative exact integers")
        self.work = 0
        self.bits = 0

    def tick(self, amount=1):
        self.work += amount
        if self.work > self.limits['max_work']:
            raise Exhausted("work budget")

    def rational(self, x):
        self.bits = max(self.bits, abs(x.numerator).bit_length(), x.denominator.bit_length())
        if self.bits > self.limits['max_integer_bits']:
            raise Exhausted("integer bit budget")
        return x

    def stats(self):
        return dict(work=self.work, max_integer_bits=self.bits)


def ratio(x):
    if type(x) is int:
        return Fraction(x)
    if type(x) is Fraction:
        return x
    if type(x) in (list, tuple) and len(x) == 2 and all(type(v) is int for v in x) and x[1] > 0:
        return Fraction(*x)
    raise ValueError("expected exact rational, excluding booleans")


def pack(x):
    return [x.numerator, x.denominator]


def _matrix(matrix, budget):
    if type(matrix) not in (list, tuple) or len(matrix) != 2 or any(type(row) not in (list, tuple) or len(row) != 2 for row in matrix):
        raise ValueError("basis must be 2 by 2")
    t = [[budget.rational(ratio(x)) for x in row] for row in matrix]
    a, b = t[0]
    c, d = t[1]
    det = budget.rational(a*d-b*c)
    budget.tick(3)
    if not det:
        raise ValueError("singular basis")
    inv = [[budget.rational(d/det), budget.rational(-b/det)],
           [budget.rational(-c/det), budget.rational(a/det)]]
    return t, inv


def _request(network, matrix, budget):
    if type(network) is not dict or set(network) != {'edges', 'rows', 'columns'}:
        raise ValueError("network keys are edges, rows, columns")
    n = network['edges']
    if type(n) is not int or n < 0:
        raise ValueError("invalid edge count")
    if n > budget.limits['max_edges']:
        raise Exhausted("edge budget")
    out = {'edges': n}
    entries = 0
    for side in ('rows', 'columns'):
        if type(network[side]) not in (list, tuple):
            raise ValueError("node collection must be a list")
        seen, nodes = [], []
        for node in network[side]:
            budget.tick()
            if type(node) is not dict or set(node) != {'ports', 'values'}:
                raise ValueError("invalid node")
            ports, values = node['ports'], node['values']
            if type(ports) not in (list, tuple) or any(type(e) is not int or not 0 <= e < n for e in ports) or len(set(ports)) != len(ports):
                raise ValueError("invalid or duplicate port")
            if len(ports) >= budget.limits['max_entries'].bit_length():
                raise Exhausted("local table budget")
            if type(values) not in (list, tuple) or len(values) != 1 << len(ports):
                raise ValueError("wrong table length")
            entries += len(values)
            if entries > budget.limits['max_entries']:
                raise Exhausted("total table budget")
            checked = [budget.rational(ratio(x)) for x in values]
            budget.tick(len(values))
            seen.extend(ports)
            nodes.append({'ports': list(ports), 'values': checked})
        if sorted(seen) != list(range(n)):
            raise ValueError("each edge must occur once on each side")
        out[side] = nodes
    t, inverse = _matrix(matrix, budget)
    return out, t, inverse


def _hash(network, matrix):
    h = sha256(b'real-affine-holant-request-v1')
    def integer(x):
        h.update(bytes([x < 0]))
        data = abs(x).to_bytes(max(1, (abs(x).bit_length()+7)//8), 'little')
        h.update(len(data).to_bytes(8, 'little'))
        h.update(data)
    def rational(x):
        integer(x.numerator)
        integer(x.denominator)
    integer(network['edges'])
    for side in ('rows', 'columns'):
        integer(len(network[side]))
        for node in network[side]:
            integer(len(node['ports']))
            for e in node['ports']:
                integer(e)
            for x in node['values']:
                rational(x)
    for row in matrix:
        for x in row:
            rational(x)
    return h.hexdigest()


def _transform(values, matrix, row, budget):
    values = list(values)
    k = len(values).bit_length()-1
    for axis in range(k):
        bit = 1 << axis
        out = list(values)
        for a in range(len(values)):
            if a & bit:
                continue
            b = a | bit
            for y, dest in ((0, a), (1, b)):
                coefficients = (matrix[0][y], matrix[1][y]) if row else matrix[y]
                out[dest] = budget.rational(values[a]*coefficients[0] + values[b]*coefficients[1])
                budget.tick(3)
        values = out
    return values


def _checker_transform(values, matrix, row, budget):
    # Separate indexing implementation: compute every output entry of an axis.
    table = list(values)
    for axis in range(len(table).bit_length()-1):
        out = []
        for y in range(len(table)):
            a = y & ~(1 << axis)
            bit = (y >> axis) & 1
            total = Fraction(0)
            for x in (0, 1):
                coefficient = matrix[x][bit] if row else matrix[bit][x]
                total += table[a | (x << axis)]*coefficient
                budget.tick(2)
            out.append(budget.rational(total))
        table = out
    return table


def transformed_network(network, matrix, **caps):
    """Utility returning exact tables; raises Exhausted or ValueError."""
    budget = Budget(caps)
    net, t, inv = _request(network, matrix, budget)
    out = {'edges': net['edges']}
    for side in ('rows', 'columns'):
        out[side] = [{'ports': node['ports'], 'values': [pack(x) for x in _transform(node['values'], t if side == 'rows' else inv, side == 'rows', budget)]} for node in net[side]]
    return out


def _basis(vectors, k, budget):
    rows = []
    for v in vectors:
        for pivot, row in rows:
            if v >> pivot & 1:
                v ^= row
            budget.tick()
        if v:
            p = (v & -v).bit_length()-1
            rows = [(a, r ^ v if r >> p & 1 else r) for a, r in rows]
            rows.append((p, v))
            rows.sort()
    return [r for _, r in rows], [p for p, _ in rows]


def _phase(linear, quadratic, t):
    return ((linear & t).bit_count() + sum((t >> i & 1)*(t >> j & 1) for i, j in quadratic)) & 1


def _recognize(values, budget):
    support = [x for x, v in enumerate(values) if v]
    if not support:
        return {'zero': True}
    origin = support[0]
    scale = values[origin]
    basis, pivots = _basis([x ^ origin for x in support], len(values).bit_length()-1, budget)
    if len(support) != 1 << len(basis):
        return None
    if any(v not in (scale, -scale) for v in values if v):
        return None
    def sign(t):
        x = origin
        for i, b in enumerate(basis):
            if t >> i & 1:
                x ^= b
        return int(values[x] == -scale)
    linear = sum(sign(1 << i) << i for i in range(len(basis)))
    quadratic = [[i, j] for i in range(len(basis)) for j in range(i+1, len(basis))
                 if sign((1 << i) | (1 << j)) ^ (linear >> i & 1) ^ (linear >> j & 1)]
    cert = dict(zero=False, origin=origin, basis=basis, pivots=pivots,
                scale=pack(scale), linear=linear, quadratic=quadratic)
    return cert if _check_local(values, cert, budget) else None


def _check_local(values, cert, budget):
    if type(cert) is not dict or type(cert.get('zero')) is not bool:
        return False
    if cert['zero']:
        return set(cert) == {'zero'} and not any(values)
    if set(cert) != {'zero', 'origin', 'basis', 'pivots', 'scale', 'linear', 'quadratic'}:
        return False
    k = len(values).bit_length()-1
    origin, basis, pivots = cert['origin'], cert['basis'], cert['pivots']
    if type(origin) is not int or not 0 <= origin < len(values) or type(basis) is not list or type(pivots) is not list or len(basis) != len(pivots):
        return False
    d = len(basis)
    if any(type(b) is not int or not 0 < b < len(values) for b in basis) or any(type(p) is not int or not 0 <= p < k for p in pivots) or len(set(pivots)) != d:
        return False
    for i, b in enumerate(basis):
        if any((b >> p & 1) != int(i == j) for j, p in enumerate(pivots)):
            return False
    scale = budget.rational(ratio(cert['scale']))
    if not scale or pack(scale) != cert['scale']:
        return False
    linear, quadratic = cert['linear'], cert['quadratic']
    if type(linear) is not int or not 0 <= linear < 1 << d or type(quadratic) is not list:
        return False
    if any(type(q) is not list or len(q) != 2 or any(type(v) is not int for v in q) or not 0 <= q[0] < q[1] < d for q in quadratic) or len({tuple(q) for q in quadratic}) != len(quadratic):
        return False
    for x, value in enumerate(values):
        t = sum(((x ^ origin) >> p & 1) << i for i, p in enumerate(pivots))
        generated = origin
        for i, b in enumerate(basis):
            if t >> i & 1:
                generated ^= b
        expected = scale * (-1 if _phase(linear, quadratic, t) else 1) if generated == x else 0
        budget.tick(1+d+len(quadratic))
        if value != expected:
            return False
    return True


def _toggle(poly, term):
    if term in poly:
        poly.remove(term)
    else:
        poly.add(term)


def _product(a, b, budget):
    out = set()
    for x in a:
        for y in b:
            _toggle(out, x | y)  # Boolean x_i^2 = x_i.
            budget.tick()
    return out


def _assemble(net, locals_, budget):
    equations, phase = [], set()
    scale = Fraction(1)
    for node, cert in zip(net['rows'] + net['columns'], locals_):
        if cert['zero']:
            return None
        ports = node['ports']
        origin, basis, pivots = cert['origin'], cert['basis'], cert['pivots']
        scale = budget.rational(scale * ratio(cert['scale']))
        local_bits = [{1 << ports[p]} ^ ({0} if origin >> p & 1 else set()) for p in pivots]
        for j, e in enumerate(ports):
            mask, rhs = 1 << e, origin >> j & 1
            for b, p in zip(basis, pivots):
                if b >> j & 1:
                    mask ^= 1 << ports[p]
                    rhs ^= origin >> p & 1
                budget.tick()
            equations.append((mask, rhs))
        for i, bits in enumerate(local_bits):
            if cert['linear'] >> i & 1:
                phase ^= bits
        for i, j in cert['quadratic']:
            phase ^= _product(local_bits[i], local_bits[j], budget)
    return equations, phase, scale


def _solve_linear(n, equations, budget):
    rows = [list(row) for row in equations]
    rank, pivots = 0, []
    for column in range(n):
        selected = next((i for i in range(rank, len(rows)) if rows[i][0] >> column & 1), None)
        budget.tick(len(rows)-rank)
        if selected is None:
            continue
        rows[rank], rows[selected] = rows[selected], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][0] >> column & 1:
                rows[i][0] ^= rows[rank][0]
                rows[i][1] ^= rows[rank][1]
            budget.tick()
        pivots.append(column)
        rank += 1
    if any(mask == 0 and rhs for mask, rhs in rows):
        return {'consistent': False}
    origin = sum(rows[i][1] << p for i, p in enumerate(pivots))
    basis = []
    for free in range(n):
        if free not in pivots:
            v = 1 << free
            for i, p in enumerate(pivots):
                if rows[i][0] >> free & 1:
                    v |= 1 << p
            basis.append(v)
    return dict(consistent=True, origin=origin, basis=basis)


def _rank(vectors, budget):
    pivots = {}
    for v in vectors:
        while v:
            p = v.bit_length()-1
            budget.tick()
            if p in pivots:
                v ^= pivots[p]
            else:
                pivots[p] = v
                break
    return len(pivots)


def _check_solution(n, equations, solution, budget):
    if type(solution) is not dict or type(solution.get('consistent')) is not bool:
        return False
    rank = _rank([m for m, b in equations], budget)
    augmented = _rank([m | (b << n) for m, b in equations], budget)
    if not solution['consistent']:
        return set(solution) == {'consistent'} and augmented > rank
    if set(solution) != {'consistent', 'origin', 'basis'} or augmented != rank:
        return False
    x, basis = solution['origin'], solution['basis']
    if type(x) is not int or not 0 <= x < 1 << n or type(basis) is not list or len(basis) != n-rank or any(type(v) is not int or not 0 < v < 1 << n for v in basis):
        return False
    if _rank(basis, budget) != len(basis):
        return False
    for m, b in equations:
        budget.tick(1+len(basis))
        if ((m & x).bit_count() & 1) != b or any((m & v).bit_count() & 1 for v in basis):
            return False
    return True


def _restrict(phase, solution, n, budget):
    affine = []
    for e in range(n):
        bits = {1 << i for i, v in enumerate(solution['basis']) if v >> e & 1}
        if solution['origin'] >> e & 1:
            bits.add(0)
        affine.append(bits)
    out = set()
    for term in phase:
        factors = [affine[i] for i in range(n) if term >> i & 1]
        if not factors:
            _toggle(out, 0)
        elif len(factors) == 1:
            out ^= factors[0]
        else:
            out ^= _product(*factors, budget)
        budget.tick(n)
    return out


def _sum_phase(d, poly, budget):
    active = set(range(d))
    trace = []
    factor = 1
    while any(t.bit_count() == 2 for t in poly):
        pair = min(t for t in poly if t.bit_count() == 2)
        i, j = [v for v in active if pair >> v & 1]
        a = {t ^ (1 << i) for t in poly if t != pair and t >> i & 1}
        b = {t ^ (1 << j) for t in poly if t != pair and t >> j & 1}
        rest = {t for t in poly if not t & pair}
        poly = rest ^ _product(a, b, budget)
        active -= {i, j}
        factor *= 2
        trace.append({'pair': [i, j], 'after': sorted(poly)})
    linear = [t for t in poly if t]
    value = 0 if linear else (-1 if 0 in poly else 1)*(factor << len(active))
    budget.rational(Fraction(value))
    return value, trace


def _check_sum(d, polynomial, trace, value, budget):
    if type(trace) is not list or type(value) is not int:
        return False
    poly = set(polynomial)
    active = set(range(d))
    for step in trace:
        if type(step) is not dict or set(step) != {'pair', 'after'} or type(step['pair']) is not list or len(step['pair']) != 2:
            return False
        i, j = step['pair']
        if type(i) is not int or type(j) is not int or i == j or i not in active or j not in active:
            return False
        pair = (1 << i) | (1 << j)
        if pair not in poly:
            return False
        # Direct coefficient partition, not the producer's set comprehensions.
        a, b, rest = set(), set(), set()
        for term in poly:
            has_i, has_j = bool(term & (1 << i)), bool(term & (1 << j))
            if has_i and has_j:
                continue
            if has_i:
                a.add(term & ~(1 << i))
            elif has_j:
                b.add(term & ~(1 << j))
            else:
                rest.add(term)
        expected = set(rest)
        for x in a:
            for y in b:
                _toggle(expected, x | y)
                budget.tick()
        after = step['after']
        if type(after) is not list or any(type(v) is not int or v < 0 or v.bit_count() > 2 or v >= 1 << d for v in after) or sorted(set(after)) != after or set(after) != expected:
            return False
        poly = expected
        active -= {i, j}
    if any(t.bit_count() == 2 for t in poly):
        return False
    expected = 0 if any(poly - {0}) else (-1 if 0 in poly else 1)*(1 << (len(trace)+len(active)))
    return value == expected


def solve_affine(network, matrix=((1, 0), (0, 1)), **caps):
    budget = Budget(caps)
    try:
        net, t, inverse = _request(network, matrix, budget)
        tables = [_transform(node['values'], t if side == 'rows' else inverse, side == 'rows', budget)
                  for side in ('rows', 'columns') for node in net[side]]
        digest = _hash(net, t)
        zero = next((i for i, values in enumerate(tables) if not any(values)), None)
        if zero is not None:
            cert = {'kind': 'zero-node', 'input_sha256': digest, 'node': zero}
            return dict(status='EXACT', value=[0, 1], certificate=cert, stats=budget.stats())
        locals_ = []
        for i, values in enumerate(tables):
            cert = _recognize(values, budget)
            if cert is None:
                return dict(status='UNSUPPORTED', value=None, certificate=None, node=i,
                            reason='transformed tensor is outside the real-affine class', stats=budget.stats())
            locals_.append(cert)
        equations, phase, scale = _assemble(net, locals_, budget)
        solution = _solve_linear(net['edges'], equations, budget)
        polynomial, trace, gauss = [], [], 0
        if solution['consistent']:
            polynomial = sorted(_restrict(phase, solution, net['edges'], budget))
            gauss, trace = _sum_phase(len(solution['basis']), set(polynomial), budget)
        value = budget.rational(scale*gauss)
        cert = dict(kind='real-affine', input_sha256=digest, locals=locals_, solution=solution,
                    polynomial=polynomial, trace=trace, gauss_sum=gauss)
        return dict(status='EXACT', value=pack(value), certificate=cert, stats=budget.stats())
    except Exhausted as e:
        return dict(status='UNKNOWN', value=None, certificate=None, reason=str(e), stats=budget.stats())


def verify_affine(network, matrix, result, **caps):
    budget = Budget(caps)
    try:
        net, t, inverse = _request(network, matrix, budget)
        if type(result) is not dict or result.get('status') != 'EXACT' or type(result.get('certificate')) is not dict:
            raise ValueError("expected an EXACT certificate")
        cert = result['certificate']
        if cert.get('input_sha256') != _hash(net, t):
            raise ValueError("external request mismatch")
        value = budget.rational(ratio(result.get('value')))
        if result['value'] != pack(value):
            raise ValueError("noncanonical value")
        tables = [_checker_transform(node['values'], t if side == 'rows' else inverse, side == 'rows', budget)
                  for side in ('rows', 'columns') for node in net[side]]
        if cert.get('kind') == 'zero-node':
            i = cert.get('node')
            if set(cert) != {'kind', 'input_sha256', 'node'} or type(i) is not int or not 0 <= i < len(tables) or any(tables[i]) or value:
                raise ValueError("invalid zero node")
        else:
            if set(cert) != {'kind', 'input_sha256', 'locals', 'solution', 'polynomial', 'trace', 'gauss_sum'} or cert['kind'] != 'real-affine' or type(cert['locals']) is not list or len(cert['locals']) != len(tables):
                raise ValueError("malformed real-affine certificate")
            for table, local in zip(tables, cert['locals']):
                if not _check_local(table, local, budget) or local['zero']:
                    raise ValueError("invalid local support or phase")
            equations, phase, scale = _assemble(net, cert['locals'], budget)
            solution = cert['solution']
            if not _check_solution(net['edges'], equations, solution, budget):
                raise ValueError("invalid global affine solution")
            if not solution['consistent']:
                if cert['polynomial'] != [] or cert['trace'] != [] or type(cert['gauss_sum']) is not int or cert['gauss_sum'] != 0 or value:
                    raise ValueError("invalid inconsistency value")
            else:
                expected = sorted(_restrict(phase, solution, net['edges'], budget))
                poly = cert['polynomial']
                if type(poly) is not list or any(type(x) is not int for x in poly) or poly != expected:
                    raise ValueError("phase restriction mismatch")
                if not _check_sum(len(solution['basis']), expected, cert['trace'], cert['gauss_sum'], budget) or value != scale*cert['gauss_sum']:
                    raise ValueError("invalid Gauss-sum proof")
        return dict(valid=True, status='VERIFIED', errors=[], stats=budget.stats())
    except Exhausted as e:
        return dict(valid=False, status='UNKNOWN', errors=[str(e)], stats=budget.stats())
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as e:
        return dict(valid=False, status='INVALID', errors=[str(e)], stats=budget.stats())


def formula_network(n, clauses, mode='sat', *, max_entries=100000):
    """Original SAT/slack incidence encoding, including repeats and unused vars.

    Repeated variable occurrences are distinct edge ports and are tied by EQ.
    Slack weights are binomial(k-1, number_true-1), not Boolean OR counts.
    """
    if type(n) is not int or n < 0 or type(clauses) not in (list, tuple) or mode not in ('sat', 'slack') or type(max_entries) is not int or max_entries < 0:
        raise ValueError("invalid formula request")
    if n > max_entries or len(clauses) > max_entries:
        raise Exhausted("formula dimension budget")
    variable_ports, columns, edge = [[] for _ in range(n)], [], 0
    total = 0
    for clause in clauses:
        if type(clause) not in (list, tuple) or any(type(lit) is not int or lit == 0 or abs(lit) > n for lit in clause):
            raise ValueError("invalid literal")
        if len(clause) >= max_entries.bit_length():
            raise Exhausted("formula table budget")
        values, ports = [], []
        for lit in clause:
            ports.append(edge)
            variable_ports[abs(lit)-1].append(edge)
            edge += 1
        for x in range(1 << len(clause)):
            true = sum(((x >> i & 1) == (lit > 0)) for i, lit in enumerate(clause))
            values.append(int(true > 0) if mode == 'sat' else (comb(len(clause)-1, true-1) if true else 0))
        total += len(values)
        if total > max_entries:
            raise Exhausted("formula total table budget")
        columns.append({'ports': ports, 'values': values})
    rows = []
    for ports in variable_ports:
        if len(ports) >= max_entries.bit_length():
            raise Exhausted("formula equality table budget")
        values = [2] if not ports else [int(x == 0 or x == (1 << len(ports))-1) for x in range(1 << len(ports))]
        total += len(values)
        if total > max_entries:
            raise Exhausted("formula total table budget")
        rows.append({'ports': ports, 'values': values})
    return {'edges': edge, 'rows': rows, 'columns': columns}


def solve_formula(n, clauses, matrix=((1, 0), (0, 1)), *, mode='sat', **caps):
    """Bind the original formula, including shared-variable equality tensors."""
    budget = Budget(caps)
    try:
        net = formula_network(n, clauses, mode, max_entries=budget.limits['max_entries'])
        return solve_affine(net, matrix, **caps)
    except Exhausted as e:
        return dict(status='UNKNOWN', value=None, certificate=None, reason=str(e), stats=budget.stats())


def verify_formula(n, clauses, matrix, result, *, mode='sat', **caps):
    """Rebuild all original tensors from the external formula before checking."""
    budget = Budget(caps)
    try:
        net = formula_network(n, clauses, mode, max_entries=budget.limits['max_entries'])
        return verify_affine(net, matrix, result, **caps)
    except Exhausted as e:
        return dict(valid=False, status='UNKNOWN', errors=[str(e)], stats=budget.stats())
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as e:
        return dict(valid=False, status='INVALID', errors=[str(e)], stats=budget.stats())
