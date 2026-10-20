# A stronger level-ten lower bound from two small scope families

This investigation proves the following **lower bound**, for every \(m\ge6\):
\[
\boxed{\min_{L_{10}}F\ \ge\ \frac{3843(2^m-1)}{16627},\qquad
       \min_{L_{10}}W\ \ge\ 1+\frac{3843(2^m-1)}{16627}.}
\]
Here the definitions are those of the [level-nine theorem](../REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md):
the coordinate zero is pinned to one, every table is supported on the
globally pinned quadratic Reed–Muller code, and \(L_{10}\) has all scopes
of total size at most ten. \(F\) is nonpin weight and \(W=1+F\).

The proof is an explicit nonnegative rational identity in necessary local
table quantities. The final selected LP has 79 nonnegative variables and
104 equalities. Independent source reconstruction and exact primal/dual
replay establish its optimum. **Its feasible optimum is not asserted to
extend to full \(L_{10}\).** This is a finite computer-checked certificate
and a mathematical transport argument, not a proof-assistant verification.
Novelty is unknown. No result about P versus NP is claimed.

## What the exact searches establish

Every search received a source-built model, without a saved basis, solution,
or requested optimum. SoPlex 8.1.0 ran in rational mode with both feasibility
and optimality tolerances zero. The independent rational LP verifier then
checked every primal equation, every dual inequality, and objective equality.
The objective in these artifacts is the singleton probability \(p\), with
**offset zero**, not \(F\) or \(W\).

| Selected necessary model | Variables | Rows | Exact minimum \(p\) |
|---|---:|---:|---:|
| Historical mixed level-nine model | 40 | 64 | \(7/31\) |
| Add \(q-8r+28v\ge0\) | 41 | 65 | \(92/407=644/2849\) |
| Add the original explicit ten-point table | 553 | 501 | \(11641/50713\) |
| Add the double-outside scope consequences instead | 59 | 80 | \(3843/16675\) |
| Combine both ten-scope constructions | 571 | 516 | \(3843/16627\) |
| Orbit-compress the preceding model | 79 | 104 | \(3843/16627\) |

Thus the single inequality cannot improve the previously proved bound.
A simple attaining point, with \(t=1/3256\), has
\[
(z_0,\ldots,z_4)=(336,126,0,0,22)t,\quad
(z_5,\ldots,z_{10})=(609,84,21,0,0,1)t,
\]
\[
(b_0,b_2,b_P,b_N,b_6,b_8)=(147,21,0,0,0,1)t,\qquad p=736t.
\]
All remaining base marginals and slacks are included in the saved primal.

Actual uniform codimension-two subspaces of \(\mathbb F_2^6\) give
\(p=5/21\); their tables were directly checked against every row of the
uncompressed models. This is an actual global-codeword control in dimension
six. The separate [virtual-dimension theorem](../REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md)
addresses higher-dimensional upper constructions; those are not certified
by the selected-model primal witnesses here.

## First new scope: an affine flat and two outside points

Average any feasible full-\(L_{10}\) solution over \(GL(m,2)\), preserving
the pin, support, consistency and objective. Use
\[
H=\{16,\ldots,23\},\qquad u=24,\quad v=32.
\]
The affine three-flat \(H\) excludes zero, and \(u,v\) are independent
modulo its four-dimensional linear span. The resulting ten-point scope
has linear span dimension six.

Use the six even-\(H\)-atom types from the level-nine theorem:
\(0,2,P,N,6,8\), with multiplicities \(1,28,14,56,28,1\).
The marginal per-atom masses are \(z_5,\ldots,z_{10}\), and \(b_i\)
is the per-atom mass with one specified outside bit equal to one.
Define
\[
\gamma_i=\Pr[H\text{ has a specified atom of type }i,\ x_u=x_v=1].
\]
Both outside single-bit marginals equal \(b_i\), by ambient symmetry.
Therefore
\[
\gamma_i\ge0,\quad d_i:=b_i-\gamma_i\ge0,\quad
e_i:=z_{5+i}-2b_i+\gamma_i\ge0,
\]
where \(i\) in \(z_{5+i}\) denotes the type's position in the six-type list.
These are actual atom masses for outside patterns \(11,10,00\).
Counting incidences gives
\[
\begin{aligned}
q&=\gamma_0+28\gamma_2+14\gamma_P+56\gamma_N+28\gamma_6+\gamma_8,\\
r&=7\gamma_2+7\gamma_P+28\gamma_N+21\gamma_6+\gamma_8,\\
v_4&=\gamma_2+3\gamma_P+12\gamma_N+15\gamma_6+\gamma_8.
\end{aligned}
\]
Here \(v_4\) denotes the old independent-four-point moment, to distinguish it
from the outside point named \(v\).

Already these equations yield the nine-term identity
\[
\begin{aligned}
16675p-3843={}&40992z_2+23424b_P+168560\gamma_P
 +426944\gamma_N+336496\gamma_6+12832\gamma_8\\
&+247296e_N+674864e_6+59408e_8.
\end{aligned}
\]
The test `test_short_identity_from_elementary_incidence_equations` checks
this directly from the 19 elementary pin/flat/mixed incidence equations,
independently of the historical quotient matrix and the optimizer's dual.
In their displayed test order, the exact multipliers are
`[3843,26901,-53802,40992,-10248,0,-10226,71582,-153412,10248,288288,0,-17780,124460,-372568,147072,0,-12040,84280]`.
The inequality \(q-8r+28v_4\ge0\) is not needed in this identity.

## Second scope and its twenty atom types

Use the original control scope in a different order:
\[
K^\times=\{4,8,12,16,20,24,28\},\qquad
O=\{1,2,32\},\qquad S=K^\times\cup O.
\]
Here \(K\) is a linear three-flat and the three outside points are
independent modulo \(K\). The pinned quadratic projection on \(S\) has
exactly 512 atoms: the seven inside bits have odd parity and all outside
bit patterns are available. The independent reviewer obtains this support
by evaluating all \(2^{21}\) pinned quadratic polynomials in dimension six.
No assumption of unrestricted support is used.

The group \(GL(K)\times S_3\) extends to ambient linear transformations.
Its five inside atom types, indexed \(i=0,\ldots,4\), are:

| \(i\) | Inside ones | Multiplicity |
|---:|---|---:|
| 0 | singleton | 7 |
| 1 | zero-sum triple | 7 |
| 2 | independent triple | 28 |
| 3 | five-set | 21 |
| 4 | all seven | 1 |

Let \(t_{i,j}\) be the mass of **one complete assignment** of inside type
\(i\) and outside weight \(j\), for \(0\le j\le3\).
It is not the total orbit mass. Hence the inside marginal relation is
\(z_i=\sum_{j=0}^3\binom3j t_{i,j}\).

For every nonempty \(A\subseteq S\) whose affine closure has at most eight
points, sum the complete assignment masses containing \(A\) and equate
this with its base selected-flat moment. Closures outside \(S\) are included.
These 435 original subset constraints reduce to 19 distinct rows after
orbit compression. All coefficients count assignments; the independent
reviewer does not import the producer's binomial coefficient formula.

## Fourteen-term certificate for the strongest bound

Using the preceding quantities:
\[
\begin{aligned}
16627p-3843={}&125552\gamma_P+146048\gamma_N+5856d_8\\
&+356160e_N+753312e_6+59664e_8\\
&+66528t_{1,3}+40992t_{2,0}+61488t_{2,1}+245616t_{2,3}\\
&+110096t_{3,1}+289072t_{3,3}
 +15728t_{4,1}+12784t_{4,3}.
\end{aligned}
\]
Every term is nonnegative. The exact equality-row multipliers are saved
in `compact_combined_run/compact_combined/integer-identity.json`; divide
them by 54 to obtain this normalization. `review_level10.py` independently
rebuilds the original local incidence rows and verifies every column and
the constant in this identity.

The compact optimum expands explicitly into a feasible point of the
571-variable raw selected model, with all 516 equalities checked. This
guards against losing assignment multiplicities in compression.

## Why the bound transports to all \(m\ge6\)

Both new scopes lie in a six-dimensional linear subspace. Restriction of
an ambient pinned quadratic polynomial to that subspace is a pinned
quadratic polynomial there; conversely every such polynomial extends by
composition with a linear projection. Thus the projection supports used
above are exactly the same in every ambient dimension \(m\ge6\).

Every necessary moment relation comes from actual scopes of size at most
ten. The seven-point inside parity uses the globally pinned code support;
it does not require adding the pin to a ten-point table. Averaging over
the ambient linear group supplies the atom invariances and common
singleton probability \(p\). Consequently
\(F=(2^m-1)p\), and the fourteen-term identity gives the stated lower bound.
Neither averaging nor an embedding supplies the missing full-\(L_{10}\)
extension of the selected optimum.

## Reproduction and evidence

From this directory:

```text
python -B review_level10.py --output FINAL_REVIEW.json
python -B -m unittest test_exploration -v
python -B -O -m unittest test_exploration -v
```

The reviewer needs no LP solver and imports no exploration producer. It
rebuilds the final original model, verifies the exact certificate, checks
the fourteen-term identity, and records source and artifact hashes before
and after replay. Tests include rebound-digest model mutations, a missing
moment row, incorrect primal/dual/objective values, changed identity
coefficients, full polynomial projection, linear-map relation preservation,
the elementary nine-term identity, the D6 controls, and raw-table expansion.

The four `*_run/RESULTS.json` records preserve all six searches, original
matrices, rational primal/dual certificates, solver output, source hashes,
and timings. `mixed_cut_run` preserves the result that the initially proposed
single cut does **not** improve the existing bound. No finite experiment here
claims to classify all ten-point geometries or determine the full relaxation.
