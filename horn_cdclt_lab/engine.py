"""Proof-producing Horn + GF(2) portfolio for the mixed-gadget audit.

The implementation deliberately exposes every theory step as a small certificate.
It is a research instrument: a DFS search engine with certifying propagation, not a
claim of a polynomial algorithm for arbitrary mixed instances.
"""
from __future__ import annotations

from itertools import product


def parity(x: int) -> int:
    return x.bit_count() & 1


def lit_var(lit: int) -> int:
    return abs(lit) - 1


def lit_value(lit: int) -> bool:
    return lit > 0


def clause_state(clause, assignment):
    """Return (satisfied, unassigned literals) for a partial assignment."""
    unassigned = []
    for lit in clause:
        v = lit_var(lit)
        if v not in assignment:
            unassigned.append(lit)
        elif assignment[v] == lit_value(lit):
            return True, []
    return False, unassigned


class HornTheory:
    """A CNF Horn relation with exact unit/conflict certificates.

    A Horn clause has at most one positive literal.  Under a partial assignment,
    ordinary Horn forward chaining is exactly repeated unit detection on these
    clauses.  The analyzer returns one step at a time so a caller can interleave
    it with other theory propagators.
    """

    def __init__(self, clauses):
        self.clauses = [tuple(int(x) for x in c) for c in clauses]
        if any(not c for c in self.clauses):
            raise ValueError("empty Horn clause is represented by an explicit conflict")
        for c in self.clauses:
            if any(-x in c for x in c):
                raise ValueError("tautological clauses are not canonical Horn clauses")
            if sum(x > 0 for x in c) > 1:
                raise ValueError(("non-Horn clause", c))

    def analyze(self, assignment):
        for i, clause in enumerate(self.clauses):
            satisfied, unassigned = clause_state(clause, assignment)
            if satisfied:
                continue
            if not unassigned:
                return [], {"kind": "horn-conflict", "clause_index": i,
                            "assignment": dict(assignment)}
            if len(unassigned) == 1:
                lit = unassigned[0]
                cert = {"kind": "horn-prop", "clause_index": i,
                        "lit": lit, "assignment": dict(assignment)}
                return [(lit_var(lit), lit_value(lit), cert)], None
        return [], None

    def verify(self, cert):
        if cert.get("kind") not in {"horn-prop", "horn-conflict"}:
            return False
        i = cert.get("clause_index")
        if not isinstance(i, int) or not (0 <= i < len(self.clauses)):
            return False
        clause = self.clauses[i]
        assignment = cert.get("assignment")
        if not isinstance(assignment, dict):
            return False
        if sum(x > 0 for x in clause) > 1:
            return False
        satisfied, unassigned = clause_state(clause, assignment)
        if satisfied:
            return False
        if cert["kind"] == "horn-conflict":
            return not unassigned
        lit = cert.get("lit")
        return len(unassigned) == 1 and unassigned[0] == lit

    def clause(self, cert):
        return self.clauses[cert["clause_index"]]


class AffineTheory:
    """GF(2) equations with Gaussian-elimination proof certificates."""

    def __init__(self, equations):
        self.equations = [(int(mask), int(rhs) & 1) for mask, rhs in equations]

    def analyze(self, assignment):
        assigned_mask = 0
        assigned_bits = 0
        for v, val in assignment.items():
            assigned_mask |= 1 << v
            if val:
                assigned_bits |= 1 << v
        basis = {}
        for i, (mask, rhs) in enumerate(self.equations):
            m = mask & ~assigned_mask
            r = rhs ^ parity(mask & assigned_bits)
            combo = 1 << i
            while m:
                pivot = m.bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = (m, r, combo)
                    break
                bm, br, bc = basis[pivot]
                m ^= bm
                r ^= br
                combo ^= bc
            if not m and r:
                return [], {"kind": "affine-conflict", "combo": combo,
                            "assignment": dict(assignment)}
        for m, r, combo in basis.values():
            if m and (m & (m - 1)) == 0:
                v = m.bit_length() - 1
                if v not in assignment:
                    return [(v, bool(r), {"kind": "affine-prop", "combo": combo,
                                          "var": v, "value": bool(r),
                                          "assignment": dict(assignment)})], None
        return [], None

    def combined(self, combo):
        mask = rhs = 0
        for i, (m, r) in enumerate(self.equations):
            if (combo >> i) & 1:
                mask ^= m
                rhs ^= r
        return mask, rhs

    def verify(self, cert):
        if cert.get("kind") not in {"affine-prop", "affine-conflict"}:
            return False
        assignment = cert.get("assignment")
        if not isinstance(assignment, dict):
            return False
        combo = cert.get("combo")
        if not isinstance(combo, int) or combo < 0 or combo >= (1 << len(self.equations)):
            return False
        mask, rhs = self.combined(combo)
        if cert["kind"] == "affine-conflict":
            return mask & ~sum(1 << v for v in assignment) == 0 and \
                   rhs ^ parity(mask & sum(1 << v for v, b in assignment.items() if b)) == 1
        v = cert.get("var")
        if not isinstance(v, int) or v in assignment:
            return False
        assigned_mask = sum(1 << x for x in assignment)
        bits = sum(1 << x for x, b in assignment.items() if b)
        return (mask & ~assigned_mask) == (1 << v) and \
               (rhs ^ parity(mask & bits)) == int(cert.get("value"))


class MixedPortfolioSolver:
    """Depth-first search with certifying Horn and affine propagation."""

    def __init__(self, nvars, horn=None, affine=None):
        self.nvars = int(nvars)
        self.horn = horn
        self.affine = affine
        self.stats = {"nodes": 0, "decisions": 0, "propagations": 0,
                      "conflicts": 0, "horn_props": 0, "affine_props": 0,
                      "horn_conflicts": 0, "affine_conflicts": 0,
                      "certificates_verified": 0}
        self.certificates = []

    def _record_conflict(self, theory_name, cert):
        theory = self.horn if theory_name == "horn" else self.affine
        assert theory is not None and theory.verify(cert)
        self.stats["certificates_verified"] += 1
        self.stats["conflicts"] += 1
        self.stats[theory_name + "_conflicts"] += 1
        self.certificates.append({"theory": theory_name, "certificate": cert})

    def _record_prop(self, theory_name, v, val, cert):
        theory = self.horn if theory_name == "horn" else self.affine
        assert theory is not None and theory.verify(cert)
        self.stats["certificates_verified"] += 1
        self.stats["propagations"] += 1
        self.stats[theory_name + "_props"] += 1
        self.certificates.append({"theory": theory_name, "certificate": cert})

    def propagate(self, assignment):
        changed = True
        while changed:
            changed = False
            if self.horn:
                props, conflict = self.horn.analyze(assignment)
                if conflict:
                    self._record_conflict("horn", conflict)
                    return False
                for v, val, cert in props:
                    if v in assignment:
                        if assignment[v] != val:
                            raise AssertionError("theory returned an inconsistent unit")
                        continue
                    self._record_prop("horn", v, val, cert)
                    assignment[v] = val
                    changed = True
                    break
                if changed:
                    continue
            if self.affine:
                props, conflict = self.affine.analyze(assignment)
                if conflict:
                    self._record_conflict("affine", conflict)
                    return False
                for v, val, cert in props:
                    if v in assignment:
                        if assignment[v] != val:
                            raise AssertionError("theory returned an inconsistent unit")
                        continue
                    self._record_prop("affine", v, val, cert)
                    assignment[v] = val
                    changed = True
                    break
        return True

    def solve(self, initial=None):
        assignment = {} if initial is None else dict(initial)
        self.stats["nodes"] += 1
        if not self.propagate(assignment):
            return None
        if len(assignment) == self.nvars:
            return assignment
        v = next(i for i in range(self.nvars) if i not in assignment)
        # A fixed deterministic branch order makes the search cost reproducible.
        self.stats["decisions"] += 1
        left = dict(assignment)
        left[v] = False
        result = self.solve(left)
        if result is not None:
            return result
        self.stats["decisions"] += 1
        right = dict(assignment)
        right[v] = True
        return self.solve(right)


def h_clauses(x, z0, z1):
    """Three Horn clauses defining H={000,110,001}."""
    return [(-x, z0), (x, -z0), (-x, -z0, -z1)]


def a_equations(y, w, z0, z1):
    """Two affine equations defining A={0100,0010,1001,1111}."""
    return [((1 << y) | (1 << z1), 0),
            ((1 << w) | (1 << z0) | (1 << z1), 1)]


def exact_one(bits):
    return sum(bits) == 1


def gadget_satisfies(x, y, w, z0, z1):
    hv = all(any((lit > 0) == [x, z0, z1][lit_var(lit)]
                 for lit in clause) for clause in h_clauses(1, 2, 3))
    av = ((y ^ z1) == 0) and ((w ^ z0 ^ z1) == 1)
    return hv and av


def gadget_projection_table():
    table = {}
    for x, y, w in product((0, 1), repeat=3):
        witnesses = []
        for z0, z1 in product((0, 1), repeat=2):
            if gadget_satisfies(x, y, w, z0, z1):
                witnesses.append((z0, z1))
        table[(x, y, w)] = witnesses
    return table


def encode_exact_one(clauses):
    """Replace every positive 1-in-3 clause by the fixed H/A gadget."""
    clauses = [tuple(int(v) for v in c) for c in clauses]
    n = 0 if not clauses else max(abs(v) for c in clauses for v in c)
    horn_clauses = []
    equations = []
    for j, (a, b, c) in enumerate(clauses):
        if min(a, b, c) <= 0 or len({a, b, c}) != 3:
            raise ValueError("positive 1-in-3 clauses need three distinct positive variables")
        x, y, w = a - 1, b - 1, c - 1
        z0, z1 = n + 2 * j, n + 2 * j + 1
        # h_clauses expects one-based literals; translate its local variables.
        horn_clauses.extend(tuple((1 if lit > 0 else -1) *
                                  ([x, z0, z1][lit_var(lit)] + 1)
                                  for lit in local)
                            for local in h_clauses(1, 2, 3))
        equations.extend(a_equations(y, w, z0, z1))
    return n + 2 * len(clauses), HornTheory(horn_clauses), AffineTheory(equations)


def direct_exact_one_sat(clauses):
    n = 0 if not clauses else max(abs(v) for c in clauses for v in c)
    for bits in product((False, True), repeat=n):
        if all(exact_one(tuple(bits[v - 1] for v in c)) for c in clauses):
            return {i: bits[i] for i in range(n)}
    return None


def encoded_sat(clauses):
    n, horn, affine = encode_exact_one(clauses)
    return MixedPortfolioSolver(n, horn=horn, affine=affine).solve()


def all_triples(n):
    return [(a, b, c) for a in range(1, n + 1)
            for b in range(a + 1, n + 1)
            for c in range(b + 1, n + 1)]
