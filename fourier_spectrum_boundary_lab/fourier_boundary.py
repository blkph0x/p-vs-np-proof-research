"""A dense Fourier-spectrum family inside ordinary 3-CNF.

The family forces x_0,...,x_{n-1} to one while leaving two private helper
variables per x_i free.  Its satisfying-function Walsh spectrum has exactly
2**n nonzero coefficients, so any method that explicitly retains only a
polynomial number of Fourier modes cannot represent all 3-CNF instances.
"""

from __future__ import annotations

from fractions import Fraction


def forced_3cnf(n):
    """Return a 3-CNF with 3n variables and 4n distinct-variable clauses."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    clauses = []
    # Variables are x_i= i, a_i=n+i, b_i=2n+i.  The four clauses enumerate
    # all signs of (a_i,b_i); their conjunction is equivalent to x_i.
    for i in range(n):
        a, b = n + i, 2 * n + i
        x = i + 1
        clauses.extend(((x, a + 1, b + 1), (x, a + 1, -(b + 1)),
                        (x, -(a + 1), b + 1), (x, -(a + 1), -(b + 1))))
    return 3 * n, tuple(clauses)


def literal_value(literal, assignment):
    """Evaluate a signed literal; variable indices are encoded as +/- (i+1)."""
    index = abs(literal) - 1
    bit = (assignment >> index) & 1
    return bool(bit) if literal > 0 else not bool(bit)


def satisfies(variable_count, clauses, assignment):
    if assignment < 0 or assignment >= (1 << variable_count):
        raise ValueError("assignment out of range")
    return all(any(literal_value(literal, assignment) for literal in clause)
               for clause in clauses)


def spectrum_coefficient(n, subset):
    """Exact normalized Walsh coefficient of the satisfying indicator.

    Character convention: chi_S(z)=(-1)**popcount(z & S), with assignment bits
    ordered as x,a,b.  The coefficient is nonzero exactly when S contains no
    helper variable, and then has magnitude 2**(-n).
    """
    variables, _ = forced_3cnf(n)
    if subset < 0 or subset >= (1 << variables):
        raise ValueError("subset out of range")
    helper_mask = ((1 << (2 * n)) - 1) << n if n else 0
    if subset & helper_mask:
        return Fraction(0)
    sign = -1 if subset.bit_count() & 1 else 1
    return Fraction(sign, 1 << n)


def spectrum_support(n):
    """Return the exact support as a compact x-variable mask description."""
    variables, _ = forced_3cnf(n)
    return tuple(range(1 << n)), variables


def fwht(values):
    """In-place unnormalized Walsh-Hadamard transform."""
    out = list(values)
    step = 1
    while step < len(out):
        for base in range(0, len(out), 2 * step):
            for j in range(step):
                u, v = out[base + j], out[base + j + step]
                out[base + j], out[base + j + step] = u + v, u - v
        step *= 2
    return out


def brute_force_spectrum(n):
    variables, clauses = forced_3cnf(n)
    values = [int(satisfies(variables, clauses, assignment))
              for assignment in range(1 << variables)]
    transformed = fwht(values)
    return tuple(Fraction(value, 1 << variables) for value in transformed)


def analytic_summary(n):
    variables, clauses = forced_3cnf(n)
    support, _ = spectrum_support(n)
    return {
        "n": n,
        "variables": variables,
        "clauses": len(clauses),
        "analytic_nonzero_coefficients": len(support),
        "input_size_linear_in_n": True,
        "coefficient_magnitude": str(Fraction(1, 1 << n)),
    }


def cyclic_unique_3cnf(n):
    """Return a linear-size exact-3-CNF with the unique model 1^n.

    For each x_i, the four sign patterns on the two cyclic successors force
    x_i=1.  For n>=3 every clause has three distinct variables, and all n
    variables are reused as helpers, so there are no auxiliary free variables.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 3:
        raise ValueError("n must be an integer at least 3")
    clauses = []
    for i in range(n):
        x = i + 1
        a = ((i + 1) % n) + 1
        b = ((i + 2) % n) + 1
        clauses.extend(((x, a, b), (x, a, -b),
                        (x, -a, b), (x, -a, -b)))
    return n, tuple(clauses)


def cyclic_unique_target_3cnf(n, target):
    """Return the cyclic exact-3-CNF whose unique model is ``target``.

    The four sign patterns on the two cyclic successors force the first
    literal in each block to be true.  Choosing its sign from ``target``
    therefore forces every variable to the requested bit while retaining
    three distinct variables in every clause.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 3:
        raise ValueError("n must be an integer at least 3")
    if isinstance(target, bool) or not isinstance(target, int) or not 0 <= target < (1 << n):
        raise ValueError("target must be an n-bit integer")
    clauses = []
    for i in range(n):
        x = i + 1
        a = ((i + 1) % n) + 1
        b = ((i + 2) % n) + 1
        forced_literal = x if ((target >> i) & 1) else -x
        clauses.extend(((forced_literal, a, b), (forced_literal, a, -b),
                        (forced_literal, -a, b), (forced_literal, -a, -b)))
    return n, tuple(clauses)


def cyclic_target_span_summary(n):
    """Exact dimension certificate for all unique-model cyclic formulas."""
    variables = cyclic_unique_target_3cnf(n, 0)[0]
    return {
        "n": n,
        "variables": variables,
        "target_count": 1 << n,
        "clauses_per_target": 4 * n,
        "indicator_span_dimension": 1 << n,
        "input_size_linear_in_n": True,
        "field_independent": True,
    }


def cyclic_spectrum_coefficient(n, subset):
    """Exact normalized Walsh coefficient for cyclic_unique_3cnf."""
    variables, _ = cyclic_unique_3cnf(n)
    if subset < 0 or subset >= (1 << variables):
        raise ValueError("subset out of range")
    sign = -1 if subset.bit_count() & 1 else 1
    return Fraction(sign, 1 << n)


def cyclic_brute_force_spectrum(n):
    variables, clauses = cyclic_unique_3cnf(n)
    values = [int(satisfies(variables, clauses, assignment))
              for assignment in range(1 << variables)]
    transformed = fwht(values)
    return tuple(Fraction(value, 1 << variables) for value in transformed)


def cyclic_analytic_summary(n):
    variables, clauses = cyclic_unique_3cnf(n)
    return {
        "n": n,
        "variables": variables,
        "clauses": len(clauses),
        "analytic_nonzero_coefficients": 1 << n,
        "input_size_linear_in_n": True,
        "unique_satisfying_assignment": (1 << n) - 1,
        "coefficient_magnitude": str(Fraction(1, 1 << n)),
    }


def modular_fwht(values, prime):
    """In-place Walsh transform over the prime field GF(prime)."""
    if isinstance(prime, bool) or not isinstance(prime, int) or prime <= 2:
        raise ValueError("prime must be an odd integer greater than two")
    out = [value % prime for value in values]
    step = 1
    while step < len(out):
        for base in range(0, len(out), 2 * step):
            for j in range(step):
                u, v = out[base + j], out[base + j + step]
                out[base + j] = (u + v) % prime
                out[base + j + step] = (u - v) % prime
        step *= 2
    return out


def cyclic_modular_spectrum(n, prime):
    """Normalized cyclic-family Walsh spectrum over GF(prime)."""
    variables, clauses = cyclic_unique_3cnf(n)
    values = [int(satisfies(variables, clauses, assignment))
              for assignment in range(1 << variables)]
    inverse = pow(pow(2, n, prime), -1, prime)
    return tuple((value * inverse) % prime
                 for value in modular_fwht(values, prime))
