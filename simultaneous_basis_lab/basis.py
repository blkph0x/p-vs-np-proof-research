"""Exact small tensor and polynomial certificates; no numerical tolerances.

The nonexistence proof also uses the classification proved in THEOREM.md.
verify_obstruction replays its finite algebraic identities, not a formal proof
of every logical step.  It does not import or trust a Groebner implementation.
Local tensor indices are little endian, with bit j the j-th port.
"""

from fractions import Fraction
import itertools
from itertools import combinations


VARIABLES = ("a", "b", "c", "d", "u")
ZERO_EXP = (0,) * len(VARIABLES)
EQ3 = (1, 0, 0, 1)
OR3 = (0, 1, 1, 1)
SLACK3 = (0, 1, 2, 1)
NAE3 = (0, 1, 1, 0)

# A local edge gauge may use a different invertible matrix on each of the
# three EQ3/OR3 wires.  The following seven support masks are the only
# zero-patterns compatible with an invertible 2 by 2 matrix (bits are a,b,c,d
# in row-major order).  The all-nonzero mask is 15.
EDGE_INVERTIBLE_SUPPORT_MASKS = (6, 7, 9, 11, 13, 14, 15)
EDGE_FLIP_MONOMIALS = ((1, 1, 0), (1, 0, 1), (1, 0, 0),
                       (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0))
EDGE_FLIP_OUTPUTS = {"even": (1, 2, 4, 7), "odd": (0, 3, 5, 6)}


def _ep_add(left, right):
    result = dict(left)
    for exponent, coefficient in right.items():
        result[exponent] = result.get(exponent, 0) + coefficient
        if not result[exponent]:
            del result[exponent]
    return result


def _ep_mul(left, right):
    result = {}
    for left_exp, left_coeff in left.items():
        for right_exp, right_coeff in right.items():
            exponent = tuple(a + b for a, b in zip(left_exp, right_exp))
            result[exponent] = result.get(exponent, 0) + left_coeff * right_coeff
    return {exponent: coefficient for exponent, coefficient in result.items() if coefficient}


def _ep_term(coefficient, exponent):
    return {tuple(exponent): coefficient} if coefficient else {}


def _ep_vector(polynomial):
    """Convert a p0,p1,p2 polynomial to the seven stored monomial slots."""
    normalized = {}
    for exponent, coefficient in polynomial.items():
        if any(exponent[3:]):
            raise ValueError("r variables remain after edge factor removal")
        normalized[tuple(exponent[:3])] = coefficient
    vector = []
    for exponent in EDGE_FLIP_MONOMIALS:
        vector.append(normalized.get(tuple(exponent), 0))
    remainder = {e: c for e, c in normalized.items() if e not in EDGE_FLIP_MONOMIALS}
    if remainder:
        raise ValueError("unexpected normalized edge-gauge monomial")
    return vector


def _edge_global_clause_data(gate):
    """Generate all normalized flip cases with exact six-variable arithmetic."""
    if gate not in ("OR3", "SLACK3"):
        raise ValueError("unknown edge-specific clause")
    values_by_weight = (0, 1, 1, 1) if gate == "OR3" else (0, 1, 2, 1)
    values = [values_by_weight[source.bit_count()] for source in range(8)]
    zero = (0, 0, 0, 0, 0, 0)
    cases = {}
    for flips in itertools.product((0, 1), repeat=3):
        adjugates = []
        for port, flipped in enumerate(flips):
            p = [0, 0, 0, 0, 0, 0]
            p[port] = 1
            r = [0, 0, 0, 0, 0, 0]
            r[3 + port] = 1
            one = _ep_term(1, zero)
            pterm = _ep_term(1, p)
            rterm = _ep_term(1, r)
            prterm = _ep_mul(pterm, rterm)
            # T=[[1,r],[p,-pr]], or T*S=[[r,1],[-pr,p]].
            if not flipped:
                matrix = ((one, rterm), (pterm, _ep_term(-1, tuple(p[i] + r[i] for i in range(6)))))
            else:
                matrix = ((rterm, one), (_ep_term(-1, tuple(p[i] + r[i] for i in range(6))), pterm))
            adjugates.append(((matrix[1][1], {e: -c for e, c in matrix[0][1].items()}),
                              ({e: -c for e, c in matrix[1][0].items()}, matrix[0][0])))
        outputs = []
        for output in range(8):
            polynomial = {}
            for source, value in enumerate(values):
                term = _ep_term(value, zero)
                for port in range(3):
                    term = _ep_mul(term, adjugates[port][(output >> port) & 1][(source >> port) & 1])
                polynomial = _ep_add(polynomial, term)
            outputs.append(polynomial)
        core = {}
        factors = {}
        for output, polynomial in enumerate(outputs):
            if not polynomial:
                core[output], factors[output] = [], [0, 0, 0]
                continue
            factor = [min(exponent[3 + j] for exponent in polynomial) for j in range(3)]
            reduced = {}
            for exponent, coefficient in polynomial.items():
                reduced[tuple(exponent[j] - (factor[j - 3] if j >= 3 else 0)
                              for j in range(6))] = coefficient
            if any(any(exponent[3:]) for exponent in reduced):
                raise AssertionError("edge factor was not a pure nonzero r monomial")
            core[output] = _ep_vector(reduced)
            factors[output] = factor
        parity_data = {}
        for parity, outputs_for_parity in EDGE_FLIP_OUTPUTS.items():
            rows = [core[output] for output in outputs_for_parity]
            constant = [sum(row[j] for row in rows) for j in range(7)]
            if constant[:6] != [0] * 6 or constant[6] not in (-4, 4):
                raise AssertionError("edge flip equations lack the constant obstruction")
            parity_data[parity] = {
                "outputs": list(outputs_for_parity), "factors": [factors[output] for output in outputs_for_parity],
                "equations": rows, "identity": [1, 1, 1, 1, constant[6]],
            }
        cases["".join(map(str, flips))] = parity_data
    return cases


def edge_specific_global_certificate(gate):
    """Certificate for every per-edge flip pattern at a degree-three clause."""
    return {
        "format": "edge-specific-eq3-clause-global-v1", "field": "complex numbers", "gate": gate,
        "invertible_support_masks": list(EDGE_INVERTIBLE_SUPPORT_MASKS),
        "eq_survivors": {str(parity): edge_eq3_parity_support_patterns(parity) for parity in (0, 1)},
        "normalized_form": "[[1,r_i],[p_i,-p_i*r_i]], p_i*r_i != 0, up to per-edge column flips",
        "monomials": [list(exponent) for exponent in EDGE_FLIP_MONOMIALS],
        "cases": _edge_global_clause_data(gate),
    }


def verify_edge_specific_global_certificate(certificate):
    try:
        if certificate.get("format") != "edge-specific-eq3-clause-global-v1":
            return False
        gate = certificate.get("gate")
        if gate not in ("OR3", "SLACK3") or certificate.get("field") != "complex numbers":
            return False
        if certificate.get("invertible_support_masks") != list(EDGE_INVERTIBLE_SUPPORT_MASKS):
            return False
        if certificate.get("eq_survivors") != {
                str(parity): edge_eq3_parity_support_patterns(parity) for parity in (0, 1)}:
            return False
        if certificate.get("normalized_form") != \
                "[[1,r_i],[p_i,-p_i*r_i]], p_i*r_i != 0, up to per-edge column flips":
            return False
        if certificate.get("monomials") != [list(exponent) for exponent in EDGE_FLIP_MONOMIALS]:
            return False
        expected = _edge_global_clause_data(gate)
        if certificate.get("cases") != expected:
            return False
        return True
    except (AttributeError, KeyError, TypeError, ValueError, IndexError, AssertionError):
        return False


def _edge_entry_nonzero(mask, row, output):
    return bool(mask >> (2 * row + output) & 1)


def edge_eq3_parity_support_patterns(parity):
    """Enumerate local zero-pattern triples surviving EQ3 parity equations.

    This is a support-only lemma.  For each required zero of the transformed
    EQ3 tensor, the two GHZ monomials must either both be structurally zero or
    both be structurally nonzero; a one-sided monomial cannot cancel.  The
    returned triples are therefore independent of coefficient values.
    """
    if parity not in (0, 1):
        raise ValueError("parity must be 0 or 1")
    targets = [y for y in range(8) if y.bit_count() % 2 != parity]
    survivors = []
    for masks in __import__("itertools").product(EDGE_INVERTIBLE_SUPPORT_MASKS, repeat=3):
        valid = True
        for output in targets:
            first = all(_edge_entry_nonzero(masks[i], 0, (output >> i) & 1)
                        for i in range(3))
            second = all(_edge_entry_nonzero(masks[i], 1, (output >> i) & 1)
                         for i in range(3))
            if first != second:
                valid = False
                break
        if valid:
            survivors.append(list(masks))
    return survivors


def _edge_specific_clause_equations(gate):
    if gate == "OR3":
        return {
            "even": [
                [1, 1, 1, -1, -1, -1, -1],
                [1, -1, -1, 1, 1, -1, -1],
                [1, -1, 1, -1, 1, -1, 1],
                [1, 1, -1, 1, -1, -1, 1],
            ],
            "odd": [
                [1, 1, 1, 1, 1, 1, 1],
                [1, -1, -1, -1, -1, 1, 1],
                [1, -1, 1, 1, -1, 1, -1],
                [1, 1, -1, -1, 1, 1, -1],
            ],
        }
    if gate == "SLACK3":
        return {
            "even": [
                [1, 1, 2, -1, -2, -2, -1],
                [1, -1, -2, 1, 2, -2, -1],
                [1, -1, 2, -1, 2, -2, 1],
                [1, 1, -2, 1, -2, -2, 1],
            ],
            "odd": [
                [1, 1, 2, 1, 2, 2, 1],
                [1, -1, -2, -1, -2, 2, 1],
                [1, -1, 2, 1, -2, 2, -1],
                [1, 1, -2, -1, 2, 2, -1],
            ],
        }
    raise ValueError("unknown edge-specific clause")


def _edge_specific_clause_certificate(gate):
    """Return an exact edge-specific EQ3/clause obstruction certificate.

    After the support lemma, every local matrix can be scaled to
    ``[[1,r_i],[p_i,-p_i*r_i]]`` with nonzero ``p_i,r_i`` and
    ``p_1*p_2*p_3=1``.  The selected clause equations, after removing nonzero
    r-factors, are recorded as coefficient vectors in the monomial order
    ``xy,xz,x,yz,y,z,1``.  Their displayed linear combinations equal ±4.
    """
    monomials = ["xy", "xz", "x", "yz", "y", "z", "1"]
    equations = _edge_specific_clause_equations(gate)
    identities = {"even": [1, 1, -1, -1, -4],
                  "odd": [1, 1, -1, -1, 4]}
    return {
        "format": "edge-specific-eq3-clause-parity-v1",
        "field": "complex numbers",
        "gate": gate,
        "invertible_support_masks": list(EDGE_INVERTIBLE_SUPPORT_MASKS),
        "eq_survivors": {
            str(parity): edge_eq3_parity_support_patterns(parity)
            for parity in (0, 1)
        },
        "normalized_form": "[[1,r_i],[p_i,-p_i*r_i]], p_i*r_i != 0, p_1*p_2*p_3=1",
        "monomials": monomials,
        "clause_equations": equations,
        "identities": identities,
    }


def edge_specific_or3_certificate():
    return _edge_specific_clause_certificate("OR3")


def edge_specific_slack_certificate():
    return _edge_specific_clause_certificate("SLACK3")


def _verify_edge_specific_clause_certificate(certificate, gate):
    """Replay the finite support lemma and ±4 polynomial contradictions."""
    try:
        if certificate.get("format") != "edge-specific-eq3-clause-parity-v1":
            return False
        if certificate.get("field") != "complex numbers":
            return False
        if certificate.get("gate") != gate:
            return False
        if certificate.get("invertible_support_masks") != list(EDGE_INVERTIBLE_SUPPORT_MASKS):
            return False
        expected_survivors = {
            str(parity): edge_eq3_parity_support_patterns(parity)
            for parity in (0, 1)
        }
        if certificate.get("eq_survivors") != expected_survivors:
            return False
        if expected_survivors != {"0": [[15, 15, 15]], "1": [[15, 15, 15]]}:
            return False
        monomials = ["xy", "xz", "x", "yz", "y", "z", "1"]
        if certificate.get("monomials") != monomials:
            return False
        equations = certificate.get("clause_equations")
        identities = certificate.get("identities")
        if set(equations) != {"even", "odd"} or set(identities) != {"even", "odd"}:
            return False
        for parity in ("even", "odd"):
            rows = equations[parity]
            identity = identities[parity]
            if type(rows) is not list or len(rows) != 4 or any(len(row) != 7 for row in rows):
                return False
            if any(type(v) is not int for row in rows for v in row):
                return False
            if type(identity) is not list or len(identity) != 5 or identity[:4] != [1, 1, -1, -1]:
                return False
            combination = [sum(identity[i] * rows[i][j] for i in range(4)) for j in range(7)]
            expected_constant = -4 if parity == "even" else 4
            if identity[4] != expected_constant or combination != [0, 0, 0, 0, 0, 0, expected_constant]:
                return False
        return certificate.get("normalized_form") == \
            "[[1,r_i],[p_i,-p_i*r_i]], p_i*r_i != 0, p_1*p_2*p_3=1"
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return False


def verify_edge_specific_or3_certificate(certificate):
    return _verify_edge_specific_clause_certificate(certificate, "OR3")


def verify_edge_specific_slack_certificate(certificate):
    return _verify_edge_specific_clause_certificate(certificate, "SLACK3")


def common_eq3_parity_branches(signature):
    """Classify rational symmetric ternary clauses compatible with EQ3 parity.

    The direct EQ3 classification in THEOREM.md says that, up to nonzero
    diagonal scaling, an even-support EQ3 basis is
    ``A_rho=[[rho,1],[1,-rho**2]]`` with ``rho**3=1``.  A column swap gives
    the odd-support cases and flips the output parity.  For a rational
    symmetric clause ``(f0,f1,f2,f3)``, this function returns every parity
    branch allowed by the exact reduced equations.  The labels ``one`` and
    ``primitive`` denote rho=1 and either primitive cube root respectively.

    The zero signature is listed in every branch because its support is
    empty.  No numerical or finite-field arithmetic is used.
    """
    if type(signature) not in (list, tuple) or len(signature) != 4:
        raise ValueError("expected four symmetric ternary entries")
    f = tuple(Fraction(value) for value in signature)
    branches = []
    if not any(f):
        one = True
        primitive = True
    else:
        # At rho=1 the two possible clause parities reduce to palindromic
        # and anti-palindromic signatures.
        one_even = f[0] == f[3] and f[1] == f[2]
        one_odd = f[0] == -f[3] and f[1] == -f[2]
        # At either primitive cube root the reduced equations force EQ3 or
        # its all-output-bit-flipped (anti-EQ3) form.
        primitive_even = f[1] == 0 and f[2] == 0 and f[0] == f[3]
        primitive_odd = f[1] == 0 and f[2] == 0 and f[0] == -f[3]
        one, primitive = False, False
    if not any(f) or one_even:
        branches.extend(({"rho": "one", "eq_support_parity": 0,
                          "clause_support_parity": 0},
                         {"rho": "one", "eq_support_parity": 1,
                          "clause_support_parity": 1}))
    if not any(f) or one_odd:
        branches.extend(({"rho": "one", "eq_support_parity": 0,
                          "clause_support_parity": 1},
                         {"rho": "one", "eq_support_parity": 1,
                          "clause_support_parity": 0}))
    if not any(f) or primitive_even:
        branches.extend(({"rho": "primitive", "eq_support_parity": 0,
                          "clause_support_parity": 0},
                         {"rho": "primitive", "eq_support_parity": 1,
                          "clause_support_parity": 1}))
    if not any(f) or primitive_odd:
        branches.extend(({"rho": "primitive", "eq_support_parity": 0,
                          "clause_support_parity": 1},
                         {"rho": "primitive", "eq_support_parity": 1,
                          "clause_support_parity": 0}))
    # Keep the JSON-facing result canonical even for the zero tensor, whose
    # four conditions overlap.
    unique = []
    for branch in branches:
        if branch not in unique:
            unique.append(branch)
    return unique


def pconst(value):
    return {ZERO_EXP: value} if value else {}


def pvar(index):
    exponent = [0] * len(VARIABLES)
    exponent[index] = 1
    return {tuple(exponent): 1}


def padd(*polynomials):
    result = {}
    for polynomial in polynomials:
        for exponent, coefficient in polynomial.items():
            result[exponent] = result.get(exponent, 0) + coefficient
    return {e: c for e, c in result.items() if c}


def pscale(polynomial, scalar):
    return {e: c * scalar for e, c in polynomial.items() if c * scalar}


def pmul(left, right):
    result = {}
    for e, c in left.items():
        for f, d in right.items():
            exponent = tuple(x + y for x, y in zip(e, f))
            result[exponent] = result.get(exponent, 0) + c * d
    return {e: c for e, c in result.items() if c}


def ppow(polynomial, power):
    result = pconst(1)
    for _ in range(power):
        result = pmul(result, polynomial)
    return result


def peval(polynomial, values):
    return sum(c * product(value ** e for value, e in zip(values, exponents))
               for exponents, c in polynomial.items())


def product(values):
    result = 1
    for value in values:
        result *= value
    return result


def pserialize(polynomial):
    return [{"powers": list(e), "coefficient": c}
            for e, c in sorted(polynomial.items())]


def pdeserialize(terms):
    result = {}
    for term in terms:
        exponent = tuple(term["powers"])
        coefficient = term["coefficient"]
        if (len(exponent) != 5 or any(type(e) is not int or e < 0 for e in exponent)
                or type(coefficient) is not int or coefficient == 0
                or exponent in result):
            raise ValueError("invalid canonical polynomial")
        result[exponent] = coefficient
    return result


def symbolic_entries(signature, orientation):
    """Full tensor summation, then check equality within each weight class."""
    a, b, c, d = (pvar(i) for i in range(4))
    if orientation == "row":
        matrix = ((a, b), (c, d))
    elif orientation == "adj_column":
        matrix = ((d, pscale(b, -1)), (pscale(c, -1), a))
    else:
        raise ValueError("unknown orientation")
    arity = len(signature) - 1
    entries = []
    for output in range(1 << arity):
        terms = []
        for original in range(1 << arity):
            term = pconst(signature[original.bit_count()])
            for port in range(arity):
                x, y = (original >> port) & 1, (output >> port) & 1
                term = pmul(term, matrix[x][y] if orientation == "row"
                            else matrix[y][x])
            terms.append(term)
        entries.append(padd(*terms))
    symmetric = [entries[(1 << k) - 1] for k in range(arity + 1)]
    assert all(entry == symmetric[index.bit_count()]
               for index, entry in enumerate(entries))
    return symmetric


def equation_systems():
    a, b, c, d, u = (pvar(i) for i in range(5))
    determinant = padd(pmul(a, d), pscale(pmul(b, c), -1))
    invertibility = padd(pmul(u, determinant), pconst(-1))
    equality = symbolic_entries(EQ3, "row")
    systems = []
    for name, signature in (("OR3", OR3), ("SLACK3", SLACK3)):
        clause = symbolic_entries(signature, "adj_column")
        for eq_parity in (0, 1):
            for clause_parity in (0, 1):
                equations = ([equality[k] for k in range(4) if k % 2 != eq_parity]
                             + [clause[k] for k in range(4) if k % 2 != clause_parity]
                             + [invertibility])
                systems.append({"gate": name, "eq_support_parity": eq_parity,
                                "clause_support_parity": clause_parity,
                                "equations": [pserialize(p) for p in equations]})
    return systems


def utrim(coefficients):
    result = list(coefficients)
    while result and result[-1] == 0:
        result.pop()
    return result


def uadd(*polynomials):
    result = [0] * max((len(p) for p in polynomials), default=0)
    for polynomial in polynomials:
        for index, coefficient in enumerate(polynomial):
            result[index] += coefficient
    return utrim(result)


def umul(left, right):
    if not left or not right:
        return []
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return utrim(result)


def upow(polynomial, power):
    result = [1]
    for _ in range(power):
        result = umul(result, polynomial)
    return result


def cube_unity_remainder(polynomial):
    result = [0, 0, 0]
    for index, coefficient in enumerate(polynomial):
        result[index % 3] += coefficient
    return utrim(result)


def substitute_normal_form(polynomial):
    """Substitute (a,b,c,d)=(rho,1,1,-rho^2), reduce rho^3=1."""
    result = []
    values = ([0, 1], [1], [1], [0, 0, -1], [])
    for exponents, coefficient in polynomial.items():
        term = [coefficient]
        for value, exponent in zip(values, exponents):
            term = umul(term, upow(value, exponent))
        result = uadd(result, term)
    return cube_unity_remainder(result)


# Ascending-degree integer lists.  Each identity is A*p + B*(rho^3-1)=K.
BEZOUT = (
    {"gate": "OR3", "weight": 0, "p": [-1, -3, -3],
     "A": [4, -3, -3], "B": [-18, -9], "K": 14},
    {"gate": "OR3", "weight": 1, "p": [1, 1, -1],
     "A": [1, 0, 1], "B": [-1, 1], "K": 2},
    {"gate": "SLACK3", "weight": 0, "p": [-1, -3, -6],
     "A": [17, -33, -3], "B": [-207, -18], "K": 190},
    {"gate": "SLACK3", "weight": 1, "p": [2, 1, -1],
     "A": [5, -1, 3], "B": [-4, 3], "K": 14},
)


def obstruction_certificate():
    return {"format": "eq3-common-basis-parity-v1", "field": "complex numbers",
            "variables": list(VARIABLES), "equation_systems": equation_systems(),
            "reduced_entries": {
                "EQ3": [substitute_normal_form(p) for p in symbolic_entries(EQ3, "row")],
                "OR3": [substitute_normal_form(p) for p in symbolic_entries(OR3, "adj_column")],
                "SLACK3": [substitute_normal_form(p) for p in symbolic_entries(SLACK3, "adj_column")]},
            "bezout": [dict(item) for item in BEZOUT]}


def verify_obstruction(certificate):
    """Replay exact identities and bind them to the original gate tensors."""
    try:
        if (certificate["format"] != "eq3-common-basis-parity-v1"
                or certificate["field"] != "complex numbers"
                or certificate["variables"] != list(VARIABLES)
                or certificate["equation_systems"] != equation_systems()):
            return False
        expected = {
            name: [substitute_normal_form(p) for p in symbolic_entries(signature, orientation)]
            for name, signature, orientation in (("EQ3", EQ3, "row"),
                                                  ("OR3", OR3, "adj_column"),
                                                  ("SLACK3", SLACK3, "adj_column"))}
        if certificate["reduced_entries"] != expected:
            return False
        seen = set()
        for identity in certificate["bezout"]:
            key = identity["gate"], identity["weight"]
            if key in seen or key not in {(g, w) for g in ("OR3", "SLACK3") for w in (0, 1)}:
                return False
            seen.add(key)
            p, A, B, K = (identity[k] for k in ("p", "A", "B", "K"))
            if any(type(c) is not int for part in (p, A, B) for c in part):
                return False
            if type(K) is not int or K == 0 or p != expected[key[0]][key[1]]:
                return False
            if uadd(umul(A, p), umul(B, [-1, 0, 0, 1])) != [K]:
                return False
        return len(seen) == 4
    except (KeyError, TypeError, ValueError, IndexError):
        return False



PRODUCT_TYPE_CERTIFICATE_FORMAT = "eq3-product-type-obstruction-v1"


def product_type_obstruction_certificate():
    """Certificate for the common product-type obstruction.

    For a symmetric ternary product-type target, a nondegenerate tensor has
    only weight 0 and weight 3 entries.  The transformed EQ3 equations for
    those two entries to be the only supported classes are g1=g2=0.  The
    zero/nonzero case split below leaves only diagonal or anti-diagonal bases;
    OR3 has three nonzero classes under either, so it is not product type.
    The displayed case split is the mathematical proof recorded in
    simultaneous_basis_lab/THEOREM.md; this function binds its exact data.
    """
    return {
        "format": PRODUCT_TYPE_CERTIFICATE_FORMAT,
        "field": "complex numbers",
        "eq3_zero_equations": ["a^2*b+c^2*d", "a*b^2+c*d^2"],
        "all_nonzero_consequence": "a*d-b*c=0",
        "invertible_zero_case_bases": ["diagonal", "anti-diagonal"],
        "surviving_zero_support_masks_abcd": [6, 9],
        "or3_support_diagonal": [0, 1, 1, 1],
        "or3_support_antidiagonal": [1, 1, 1, 0],
        "slack3_support_diagonal": [0, 1, 1, 1],
        "slack3_support_antidiagonal": [1, 1, 1, 0],
        "conclusion": "no common invertible basis maps EQ3 with OR3 or SLACK3 to symmetric product-type signatures",
    }


def verify_product_type_obstruction(certificate):
    """Replay the exact support data and representative transformations."""
    try:
        if certificate.get("format") != PRODUCT_TYPE_CERTIFICATE_FORMAT:
            return False
        if certificate.get("field") != "complex numbers":
            return False
        if certificate.get("eq3_zero_equations") != ["a^2*b+c^2*d", "a*b^2+c*d^2"]:
            return False
        if certificate.get("all_nonzero_consequence") != "a*d-b*c=0":
            return False
        if certificate.get("invertible_zero_case_bases") != ["diagonal", "anti-diagonal"]:
            return False
        if certificate.get("surviving_zero_support_masks_abcd") != [6, 9]:
            return False
        survivors = []
        for mask in range(16):
            nz = [(mask >> i) & 1 for i in range(4)]
            a, b, c, d = nz
            if not (a or b) or not (c or d) or not (a or c) or not (b or d):
                continue
            terms_g1 = [a and b, c and d]
            terms_g2 = [a and b, c and d]
            if sum(bool(v) for v in terms_g1) == 1 or sum(bool(v) for v in terms_g2) == 1:
                continue
            if mask != 15:
                survivors.append(mask)
        if survivors != [6, 9]:
            return False
        if certificate.get("or3_support_diagonal") != [0, 1, 1, 1]:
            return False
        if certificate.get("or3_support_antidiagonal") != [1, 1, 1, 0]:
            return False
        if certificate.get("slack3_support_diagonal") != [0, 1, 1, 1]:
            return False
        if certificate.get("slack3_support_antidiagonal") != [1, 1, 1, 0]:
            return False
        if not certificate.get("conclusion"):
            return False
        diagonal = ((Fraction(2), 0), (0, Fraction(3)))
        anti = ((0, Fraction(2)), (Fraction(3), 0))
        for signature in (OR3, SLACK3):
            for matrix, expected in ((diagonal, [0, 1, 1, 1]),
                                     (anti, [1, 1, 1, 0])):
                transformed = symmetric_table(transform(signature, inverse2(matrix), "column"))
                if [int(value != 0) for value in transformed] != expected:
                    return False
        return True
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return False

def inverse2(matrix):
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise ValueError("expected 2 by 2 matrix")
    a, b, c, d = map(Fraction, (matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1]))
    determinant = a * d - b * c
    if not determinant:
        raise ValueError("singular basis")
    return ((d / determinant, -b / determinant), (-c / determinant, a / determinant))


def expand_symmetric(signature):
    arity = len(signature) - 1
    return [Fraction(signature[index.bit_count()]) for index in range(1 << arity)]


def transform(signature, matrix, orientation):
    if orientation not in ("row", "column"):
        raise ValueError("unknown orientation")
    original = expand_symmetric(signature)
    arity = len(signature) - 1
    result = []
    for output in range(1 << arity):
        total = Fraction(0)
        for source, value in enumerate(original):
            term = value
            for port in range(arity):
                x, y = (source >> port) & 1, (output >> port) & 1
                term *= Fraction(matrix[x][y] if orientation == "row" else matrix[y][x])
            total += term
        result.append(total)
    return result


def symmetric_table(entries):
    arity = (len(entries) - 1).bit_length()
    if len(entries) != 1 << arity:
        raise ValueError("tensor length must be a power of two")
    result = [entries[(1 << k) - 1] for k in range(arity + 1)]
    if any(value != result[index.bit_count()] for index, value in enumerate(entries)):
        raise ValueError("not symmetric")
    return result


def support_parities(entries):
    return sorted({index.bit_count() % 2 for index, value in enumerate(entries) if value})


def even_graph(A, B):
    """Planar K4, exterior triangle 0,1,2 and interior center 3."""
    A, B = Fraction(A), Fraction(B)
    if not B:
        raise ValueError("this explicit realization requires nonzero B")
    return {"vertices": 4, "ports": [0, 1, 2],
            "embedding": "outer triangle 0,1,2; center 3 inside",
            "edges": [(i, j, A / (3 * B)) for i, j in combinations(range(3), 2)]
                     + [(i, 3, B) for i in range(3)]}


def odd_graph(A, B):
    """Exterior triangle plus a separate forced internal edge, drawn inside."""
    A, B = Fraction(A), Fraction(B)
    if not B:
        raise ValueError("this explicit realization requires nonzero B")
    return {"vertices": 5, "ports": [0, 1, 2],
            "embedding": "outer triangle 0,1,2; separate edge 3,4 inside",
            "edges": [(i, j, A / B) for i, j in combinations(range(3), 2)] + [(3, 4, B)]}


def matching_signature(graph):
    """Enumerate edge subsets independently of a recursive matching algorithm."""
    edges = graph["edges"]
    result = []
    for deleted in range(1 << len(graph["ports"])):
        remaining = set(range(graph["vertices"])) - {
            port for i, port in enumerate(graph["ports"]) if (deleted >> i) & 1}
        total = Fraction(0)
        for selected in range(1 << len(edges)):
            covered = set()
            weight = Fraction(1)
            valid = True
            for index, (left, right, edge_weight) in enumerate(edges):
                if not (selected >> index) & 1:
                    continue
                if left not in remaining or right not in remaining or left in covered or right in covered:
                    valid = False
                    break
                covered.update((left, right))
                weight *= Fraction(edge_weight)
            if valid and covered == remaining:
                total += weight
        result.append(total)
    return result


def positive_controls():
    H = ((1, 1), (1, -1))
    or_basis = ((1, 0), (Fraction(1, 2), 1))
    slack_basis = ((1, 0), (1, 1))
    definitions = (
        ("EQ3 row under H", EQ3, H, "row", even_graph(2, 2)),
        ("EQ3 column under inverse H", EQ3, H, "column", even_graph(Fraction(1, 4), Fraction(1, 4))),
        ("NAE3 column under inverse H", NAE3, H, "column", even_graph(Fraction(3, 4), Fraction(-1, 4))),
        ("OR3 individually", OR3, or_basis, "column", odd_graph(1, Fraction(1, 4))),
        ("SLACK3 individually", SLACK3, slack_basis, "column", odd_graph(1, -2)),
    )
    result = []
    for name, signature, basis, orientation, graph in definitions:
        entries = transform(signature, basis if orientation == "row" else inverse2(basis), orientation)
        replay = matching_signature(graph)
        assert replay == entries
        result.append({"name": name, "signature": list(signature), "basis": basis,
                       "orientation": orientation, "transformed": entries,
                       "symmetric_transformed": symmetric_table(entries),
                       "graph": graph, "graph_signature": replay,
                       "eq3_row_under_same_basis": transform(EQ3, basis, "row")})
    return result
