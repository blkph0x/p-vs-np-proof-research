# Uniform PHP resolution-width certificate

This report formalizes and checks the standard pigeonhole family
PHP\((n+1,n)\). It is a proof-complexity result for resolution, not a claim
about arbitrary SAT algorithms.

## Encoding

For pigeons \(i\in[n+1]\) and holes \(j\in[n]\), the variable
\(p_{i,j}\) means that pigeon \(i\) uses hole \(j\). The repository's
standard CNF contains:

* the positive clause \(p_{i,1}\lor\cdots\lor p_{i,n}\) for every pigeon;
* same-pigeon exclusivity clauses
  \(\lnot p_{i,j}\lor\lnot p_{i,k}\);
* hole exclusivity clauses \(\lnot p_{i,j}\lor\lnot p_{k,j}\).

The certificate uses only the positive clauses and the hole-exclusivity
clauses. Therefore it is valid for the stronger repository encoding that also
contains the same-pigeon clauses.

## Constructive upper bound

The construction follows Proposition 4.1 in Stefan Dantchev's dissertation,
[On Resolution Complexity of Matching Principles](https://www.brics.dk/DS/02/2/BRICS-DS-02-2.pdf),
Chapter 4. For every injection \(\pi:[k]\to[n]\), define the stage-
\(k\) clause

\[
C_{k,\pi}=\{\lnot p_{1,\pi(1)},\ldots,\lnot p_{k,\pi(k)}\}.
\]

There are \(n!/(n-k)!\) such clauses. Stage \(n\) is obtained by resolving
the positive axiom for pigeon \(n+1\) against the \(n\) hole-exclusivity
axioms selected by a permutation \(\pi\). To pass from stage \(k+1\) to
stage \(k\), first resolve the positive axiom for pigeon \(k+1\) against
the hole axioms selected by \(\pi\). This leaves positive literals for
holes outside \(\operatorname{range}(\pi)\). Resolve those literals away
using the stage \(k+1\) clauses for the extensions
\(\pi\cup\{k+1\mapsto j\}\). At stage zero this produces the empty clause.

Every intermediate clause has at most \(n\) literals, and every stage clause
has at most \(n\) literals. The number of resolution steps is exactly

\[
n\sum_{k=0}^{n}\frac{n!}{(n-k)!}=2^{O(n\log n)}.
\]

`php_width_proof.py` emits the complete DAG with parent references. The
certificate stores the original clauses, every axiom reference, every pivot,
and the derived clause at each step.

## Matching lower bound

For \(n\ge2\), a resolution refutation of width less than \(n\) cannot use a
positive PHP axiom, because each has width \(n\). The remaining initial
clauses are negative and are all satisfied by the all-false assignment.
Resolution and weakening preserve satisfaction of an assignment, so a proof
using only those clauses cannot derive the empty clause. Thus every refutation
has width at least \(n\). The construction above gives width at most \(n\),
so the minimum resolution width is exactly \(n\) for every \(n\ge2\).

PHP\((2,1)\) is a degenerate edge case: its hole-exclusivity axiom already
has width two, and its minimum width is two.

## Independent replay

`review_php_width_proof.py` reconstructs the variable numbering and complete
CNF independently. It checks that every axiom is present in that formula,
that every parent precedes its resolution conclusion, that each pivot has
opposite signs, and that the recorded conclusion is the exact resolvent. It
also checks the stage counts, per-stage resolution counts, final empty clause,
and maximum width.

The saved campaign covers \(n=1,\ldots,6\) and saves the full \(n=6\)
certificate. The \(n=6\) replay has 11,742 resolution steps and 11,875
proof events, extending the machine-checked finite anchor without changing
the all-size construction or claiming a polynomial-size refutation:

| holes \(n\) | pigeons | variables | stage counts \(k=0\ldots n\) | resolution steps | max width |
| ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 2 | 2 | 1, 1 | 2 | 2 |
| 2 | 3 | 6 | 1, 2, 2 | 10 | 2 |
| 3 | 4 | 12 | 1, 3, 6, 6 | 48 | 3 |
| 4 | 5 | 20 | 1, 4, 12, 24, 24 | 260 | 4 |
| 5 | 6 | 30 | 1, 5, 20, 60, 120, 120 | 1,630 | 5 |
| 6 | 7 | 42 | 1, 6, 30, 120, 360, 720, 720 | 11,742 | 6 |

The machine-readable outputs are
[`PHP_WIDTH_RESULTS.json`](PHP_WIDTH_RESULTS.json),
[`PHP_WIDTH_CERTIFICATE_N6.json`](PHP_WIDTH_CERTIFICATE_N6.json), and
[`PHP_WIDTH_REVIEW.json`](PHP_WIDTH_REVIEW.json). Re-run them with:

```text
python run_php_width.py
python -m unittest -v test_resolution.py
```

This uniform width theorem does not give a polynomial-time SAT solver. Its
explicit proof has super-polynomial size in the pigeonhole parameter, and
resolution is one proof system rather than a lower bound against all possible
algorithms or proof systems. The result narrows the behavior of this exact
proof-producing route while leaving P versus NP unresolved.
