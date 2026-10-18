# A common complex basis cannot make EQ3 and either ternary clause factor have matchgate parity

## Statement and model

Let `G=EQ3=[1,0,0,1]` be a symmetric row tensor. Consider either column tensor
`R=OR3=[0,1,1,1]` or `R=SLACK3=[0,1,2,1]`, where an entry is indexed by the
number of input ones, not by a binomially weighted coefficient. There is **no
invertible complex 2 by 2 matrix T** for which both

`G'=G T^(tensor 3)` and `R'=(T^-1)^(tensor 3) R`

are supported on a single Hamming-weight parity. Each tensor is allowed its
own parity. Therefore neither pair can be simultaneously realized as planar
matchgate signatures by this one common basis acting on every port.

This proves only a necessary-parity obstruction for this specified encoding
and basis model. It does not resolve P versus NP, assert a new classification,
exclude all holographic algorithms, or exclude other encodings, larger
domains, different transformations at different occurrences, or nonmatchgate
tractable families. We make no positive-characteristic statement. The proof
holds over C and thus also excludes real and rational bases.

The definitions are those of Cai and Gorenstein, *Matchgates Revisited*,
[Section 2](https://arxiv.org/html/1303.6729#S2). A signature entry is the
weighted sum of perfect matchings after deleting the indicated external
vertices, which lie on the outer face in their specified order. Deleting
vertices of the wrong parity leaves an odd number of vertices, so every
such entry is zero, even for complex edge weights. We use this necessary
condition only, without invoking sufficiency or a signature classification.

The local flat index is little endian, `index=sum(bit[j]*2^j)`. These initial
tensors are symmetric, so changing port order does not change the algebra.
The row/column actions use opposite inverses; using the same action on both
sides would be a different problem and would not preserve edge contraction.

## All polynomial equations, including invertibility

Write

```
T = [[a,b],[c,d]],   Delta=ad-bc,
adj(T) = [[d,-b],[-c,a]].
```

For zero equations, replace `T^-1` by `adj(T)`: the omitted factor
`Delta^-3` is nonzero. It may not be omitted when comparing counts.
The four symmetric row entries are

```
g0 = a^3+c^3
g1 = a^2*b+c^2*d
g2 = a*b^2+c*d^2
g3 = b^3+d^3.
```

For OR3, the adjugate column entries are

```
r0 = -b^3+3*b^2*d-3*b*d^2
r1 = a*b^2-2*a*b*d+a*d^2-b^2*c+2*b*c*d
r2 = -a^2*b+a^2*d+2*a*b*c-2*a*c*d-b*c^2
r3 = a^3-3*a^2*c+3*a*c^2.
```

For SLACK3 they are

```
s0 = -b^3+6*b^2*d-3*b*d^2
s1 = a*b^2-4*a*b*d+a*d^2-2*b^2*c+2*b*c*d
s2 = -a^2*b+2*a^2*d+4*a*b*c-2*a*c*d-b*c^2
s3 = a^3-6*a^2*c+3*a*c^2.
```

For each `h=r` and `h=s`, the four complete systems below set every listed
polynomial to zero. Thus there are eight systems, each with five equations.
The extra variable `u` enforces invertibility exactly over C.

| EQ3 support | Clause support | Five zero polynomials |
|---|---|---|
| even | even | `g1, g3, h1, h3, u*(ad-bc)-1` |
| even | odd | `g1, g3, h0, h2, u*(ad-bc)-1` |
| odd | even | `g0, g2, h1, h3, u*(ad-bc)-1` |
| odd | odd | `g0, g2, h0, h2, u*(ad-bc)-1` |

One way to derive these expressions is to encode a symmetric column tensor
as `F(X,Y)=sum_k binom(3,k)*R_k*X^(3-k)*Y^k` and substitute
`(X,Y)=(dX-cY,-bX+aY)`. The code independently generates every entry by
the full tensor sum before collapsing equal weight classes. Tests compare
the resulting polynomials with the formulas above coefficient by coefficient.

## Classification of every parity-admissible EQ3 basis

First assume `G'` has even support, so `g1=g3=0`.

1. From `b^3+d^3=0`, either both `b,d` vanish or neither does. The former
   contradicts invertibility. Hence `b,d` are nonzero.
2. From `a^2*b+c^2*d=0`, either both `a,c` vanish or neither does. Again,
   invertibility forbids the former. Hence `a,c` are nonzero.
3. Set `rho=a/c` and `tau=d/b`. The equations give
   `tau^3=-1` and `tau=-rho^2`, hence `rho^6=1`.
4. The determinant is `bc*(rho*tau-1)=-bc*(rho^3+1)`. Invertibility
   excludes `rho^3=-1`. Because `(rho^3-1)*(rho^3+1)=0`, it follows that
   `rho^3=1`.

Consequently every such matrix is exactly

```
T = A_rho D,
A_rho = [[rho,1],[1,-rho^2]],
D = diag(c,b),     rho^3=1,     b*c != 0.
```

Conversely each such matrix is invertible, since `det(A_rho)=-2`, and has
even row support: the reduced EQ3 entries are `[2,0,2*rho,0]`.

Multiplying columns of T by nonzero diagonal entries preserves the zero
pattern of the row tensor. For the column tensor,
`adj(A_rho D)=adj(D) adj(A_rho)`; `adj(D)=diag(b,c)` multiplies each output
entry by a nonzero factor. Thus diagonal scaling also preserves its zero
pattern. It suffices to study `A_rho`.

Let `S=[[0,1],[1,0]]`. Swapping the columns of T flips every output bit of
the row tensor. At arity three this exchanges the two parities. Therefore
every invertible basis with odd EQ3 support has the form `A_rho S D`
for a nonzero diagonal D. On the clause side,
`adj(A_rho S)=adj(S) adj(A_rho)=-S adj(A_rho)`, which flips all output bits
and contributes one global minus sign after the tensor cube. This also
interchanges the two parities. A clause with entries in both parities
remains mixed. This reduces every one of the eight branches to the case
`A_rho`, without a finite search or an assumption that the basis is real.

## Exact nonvanishing certificates

Substitute `(a,b,c,d)=(rho,1,1,-rho^2)` in the adjugate clause entries and
reduce modulo `Q=rho^3-1`. The resulting entries are

| Gate | Weight 0 | Weight 1 | Weight 2 | Weight 3 |
|---|---|---|---|---|
| OR3 | `-1-3rho-3rho^2` | `1+rho-rho^2` | `1+rho-rho^2` | `1+3rho-3rho^2` |
| SLACK3 | `-1-3rho-6rho^2` | `2+rho-rho^2` | `1+2rho-rho^2` | `1+3rho-6rho^2` |

For each polynomial p in the weight-0 and weight-1 columns, the following
integer identity holds identically in rho: `A*p+B*Q=K`.

| p | A | B | K |
|---|---|---|---|
| `-1-3rho-3rho^2` | `4-3rho-3rho^2` | `-18-9rho` | 14 |
| `1+rho-rho^2` | `1+rho^2` | `-1+rho` | 2 |
| `-1-3rho-6rho^2` | `17-33rho-3rho^2` | `-207-18rho` | 190 |
| `2+rho-rho^2` | `5-rho+3rho^2` | `-4+3rho` | 14 |

When `Q=0`, each nonzero constant K proves that p cannot be zero over C.
Thus each clause has a nonzero even entry and a nonzero odd entry for every
allowed rho. Diagonal scaling and column swapping cannot remove this fact.
This proves all eight systems inconsistent.

The constants are small enough that each identity can be checked simply by
multiplication. `verify_obstruction` performs that check with integer list
arithmetic, regenerates all full tensor polynomials, and binds each p to the
proper transformed entry. It does not import SymPy. The proof also relies
on the classification argument above; this is an exact mathematical proof
with replayed arithmetic, not a claim that a proof assistant verified every
logical step. No untrusted Groebner assertion is needed for the conclusion.

## Classification of every rational symmetric ternary clause

The same EQ3 classification gives a broader obstruction than the two named
clauses. Let a rational symmetric ternary column signature be

```
F = [f0, f1, f2, f3].
```

For an even-support EQ3 basis, use `A_rho` above. Direct tensor summation for
the adjugate column action, reduced with `rho^3=1`, gives the four output
weight classes

```
q0 = -f0 - 3*f1*rho - 3*f2*rho^2 - f3
q1 = -f0*rho - f1*rho^2 + f2 + f3*rho
q2 = -f0*rho^2 + f1 + f2*rho - f3*rho^2
q3 = -f0 + 3*f1*rho - 3*f2*rho^2 + f3.
```

For `rho=1`, the even clause branch (`q1=q3=0`) is exactly
`f0=f3` and `f1=f2`; the odd clause branch (`q0=q2=0`) is exactly
`f0=-f3` and `f1=-f2`. For either primitive cube root, zeroing the even
entries forces `f1=f2=0` and `f0=f3`, while zeroing the odd entries forces
`f1=f2=0` and `f0=-f3`. These statements follow by solving the displayed
linear equations over `Q`: at a primitive root, a rational polynomial
`u+v*rho+w*rho^2` vanishes exactly when `u=v=w`.

Therefore every rational symmetric clause that shares a parity basis with EQ3
belongs to one of four families (with the zero signature included):

| EQ3 normal parameter | clause parity | exact family |
|---|---:|---|
| `rho=1` | even | `[u,v,v,u]` |
| `rho=1` | odd | `[u,v,-v,-u]` |
| primitive `rho` | even | `[u,0,0,u]` |
| primitive `rho` | odd | `[u,0,0,-u]` |

A column swap changes both support parities and does not enlarge these four
families. Nonzero diagonal scaling also preserves their zero patterns. Thus OR3
`[0,1,1,1]` and the slack factor `[0,1,2,1]` fail immediately because they are
neither palindromic nor anti-palindromic, and they are not EQ3/anti-EQ3. The
classification applies only to rational **symmetric ternary** clauses and the
same common 2 by 2 row/column action; it does not claim a theorem for
non-symmetric signatures, other encodings, or arbitrary holographic bases.

`common_eq3_parity_branches` implements these four exact tests using rational
arithmetic. The tests enumerate all 81 signatures in `{-1,0,1}^4` and replay
the `rho=1` branches with direct Hadamard tensor transforms. This is an exact
classification argument, not a numerical search over bases.

## Edge-specific gauges do not rescue EQ3 with OR3

The common-basis restriction can be relaxed further. Give the three wires of
the equality tensor independent invertible matrices

```
T_i = [[a_i,b_i],[c_i,d_i]],  i=1,2,3,
```

and transform the clause with the contragredient matrices `T_i^-1` on its
three ports. This is the most general per-edge gauge that preserves a tensor
contraction. There is still no choice making both transformed EQ3 and OR3
supported on single parities.

First consider an EQ3 output parity. An invertible matrix can have only the
following seven zero/nonzero support masks (bits are `a,b,c,d` in row-major
order):

```
0110, 0111, 1001, 1011, 1101, 1110, 1111.
```

Each required zero of transformed EQ3 is a sum of two GHZ monomials. If one
monomial is structurally zero and the other is not, cancellation is
impossible. Checking the seven masks on each of the three ports leaves exactly
one triple for either target parity:

```
(1111,1111,1111).
```

Thus every entry of every `T_i` is nonzero. For even EQ3 support, scale each
matrix by `a_i^-1` and write

```
T_i = [[1,r_i],[p_i,q_i]],  p_i*r_i != 0.
```

The four odd EQ3 entries vanish exactly when, with `P=p1*p2*p3`,

```
q1 = -r1*p1/P,  q2 = -r2*p2/P,  q3 = -r3*p3/P,
P^2 = 1.
```

Invertibility gives `det(T_i)=-r_i*p_i*(1/P+1)`, so `P=-1` is forbidden and
therefore `P=1` and `q_i=-p_i*r_i`. (An odd EQ3 target is obtained by flipping
one output bit, which only swaps the two clause parities below.)

Put `x=p1`, `y=p2`, `z=p3`. After applying the adjugates to OR3 and deleting
nonzero factors in the `r_i`, the four equations for an even OR3 target are

```
E1 = xy+xz+x-yz-y-z-1
E2 = xy-xz-x+yz+y-z-1
E3 = xy-xz+x-yz+y-z+1
E4 = xy+xz-x+yz-y-z+1.
```

They satisfy the polynomial identity

```
E1 + E2 - E3 - E4 = -4.
```

For an odd OR3 target the equations are

```
O1 = xy+xz+x+yz+y+z+1
O2 = xy-xz-x-yz-y+z+1
O3 = xy-xz+x+yz-y+z-1
O4 = xy+xz-x-yz+y+z-1,
```

and

```
O1 + O2 - O3 - O4 = 4.
```

Either identity contradicts simultaneous vanishing over the complex numbers.
Flipping one output bit handles odd EQ3 and merely exchanges these two
contradictions. This proves the aligned three-wire local calculation. The
certificate `edge_specific_or3_certificate` replays the seven-mask support
enumeration and both constant identities; the independent review also
regenerates the tensor equations symbolically.

The calculation extends to a whole incidence network whose equality nodes all
have degree three. At each equality node, flip one output bit if necessary to
normalize its parity to even. This puts every incident edge matrix in the
displayed form, up to a column flip on that edge. Consequently an OR3 clause
sees one of the eight flip patterns `000` through `111`. For every pattern and
for both clause parities, the exact four reduced equations are generated by
the saved `edge_specific_global_certificate`; after removing nonzero `r_i`
monomials, their four coefficient vectors sum to `-4` (even target) or `4`
(odd target). Thus no assignment of independent edge gauges can make every
degree-three equality and OR3 clause parity-supported in such a network.

The same normalized calculation covers the slack clause `[0,1,2,1]`. Its four
even-branch equations are

```
S1 = xy+xz+2x-yz-2y-2z-1
S2 = xy-xz-2x+yz+2y-2z-1
S3 = xy-xz+2x-yz+2y-2z+1
S4 = xy+xz-2x+yz-2y-2z+1,
```

and its odd-branch equations are

```
T1 = xy+xz+2x+yz+2y+2z+1
T2 = xy-xz-2x-yz-2y+2z+1
T3 = xy-xz+2x+yz-2y+2z-1
T4 = xy+xz-2x-yz+2y+2z-1.
```

They obey `S1+S2-S3-S4=-4` and `T1+T2-T3-T4=4`. The same eight flip patterns
therefore exclude a degree-three equality/slack incidence network as well.
The saved certificates contain both clause systems; the independent replay
checks all 128 normalized equations across the two gates and eight patterns.

This is still a necessary-parity obstruction for one binary encoding. It does
not exclude larger domains, non-parity tractable signatures, gadgets that
change the encoding, or arbitrary algorithms for SAT.

SymPy Groebner computations return `[1]` for each five-equation system and
are saved only as corroboration. They are not substituted for the direct
proof and the four explicit identities.

## The common product-type route is also blocked

The affine and product-type Holant families are separate from matchgates. The
primary definitions and the symmetric product-type classification are in Cai,
Guo and Williams, [Holographic Algorithms Beyond Matchgates](https://arxiv.org/html/1307.7430#S2). For this ternary symmetric setting, the product-type classification says that a
nondegenerate symmetric ternary signature has support only at Hamming weights
0 and 3, so a transformed EQ3 tensor would have to satisfy

```
g1 = a^2*b + c^2*d = 0,
g2 = a*b^2 + c*d^2 = 0.
```

These two equations have a short exact case split over the complex numbers.
If `a,b,c,d` are all nonzero, division of the first equation by the second
gives `a/b=c/d`, hence `ad-bc=0`, contradicting invertibility. If any entry
is zero, the equations plus a nonzero determinant leave only a diagonal matrix
(`b=c=0`) or an anti-diagonal matrix (`a=d=0`).

Under a diagonal basis, the contragredient OR3 tensor keeps support
`[0,1,1,1]`, up to nonzero scalings, and SLACK3 keeps the same support because its
weight-1 and weight-2 entries are both nonzero. Under an anti-diagonal basis, each keeps the
complementary support `[1,1,1,0]`. Neither OR3 nor SLACK3 has only weight 0 and weight 3
entries, so neither clause is product type in either surviving case. EQ3 itself has
tensor rank two; therefore an invertible local basis cannot turn it into a
rank-one degenerate product of unary signatures, which is the only other
symmetric product-type possibility. The saved
`product_type_obstruction_certificate` records this case split and replays the
support conclusions with exact rational representatives.

Thus the standard common binary holographic search now has two independently
scoped exclusions: matchgate parity and product type. This still does not
exclude larger domains, non-symmetric encodings, other tractable families, or
arbitrary SAT algorithms, and it is not a P-versus-NP lower bound.

## Genuine positive controls

Let `H=[[1,1],[1,-1]]`, so `H^-1=H/2`. Exact tensor multiplication gives

```
EQ3 (row) under H:              [2,0,2,0]
EQ3 (column) under H^-1:        [1/4,0,1/4,0]
NAE3=[0,1,1,0] under H^-1:      [3/4,0,-1/4,0].
```

These are actual planar matchgate signatures, not merely parity tests.
For a signature `[A,0,B,0]` with `B!=0`, put three external vertices on
an outer triangle, add one internal center, set each spoke weight to B,
and each triangle-edge weight to `A/(3B)`. The full K4 graph has three
perfect matchings whose weights sum to A. Deleting any two external
vertices leaves one spoke of weight B. Other deletions leave odd order.
This realizes all three signatures above, and proves genuine shared-basis
controls for the pairs EQ3/EQ3 and EQ3/NAE3. Signed rational weights are
allowed; the NAE3 control uses them.

The clauses that fail jointly with EQ3 also succeed individually:

```
T_OR=[[1,0],[1/2,1]]:
  OR3 column under T_OR^-1 = [0,1,0,1/4],
  EQ3 row under T_OR       = [9/8,1/4,1/2,1].

T_slack=[[1,0],[1,1]]:
  SLACK3 column under T_slack^-1 = [0,1,0,-2],
  EQ3 row under T_slack          = [2,1,1,1].
```

For `[0,A,0,B]`, take an outer triangle with every edge weight `A/B`
and an additional disjoint internal edge of weight B, drawn inside the
triangle. Deleting one external vertex leaves the opposite triangle edge
and the mandatory internal edge, giving A. Deleting all three gives B.
The other parity is zero. This explicit plane graph realizes the two
individual clause controls. Its disconnected component does not touch
the external vertices or change their order. In both individual controls
the transformed EQ3 tensor has both parities and therefore fails.

The runner enumerates every edge subset of these five small graphs and
replays all 40 boundary sums exactly as fractions. It also uses the actual
inverse matrices, preserving all determinant scale factors.

## Consequence for the next search

The proposed general encoding already includes EQ3 and a positive,
unnegated ternary clause. Because that base pair is impossible, adding
literal polarities or other copy arities cannot produce a common basis.
There is no successful candidate here to extend to the larger gate set.
The positive controls alone make no claim about those extra gates, arbitrary
network planarity, crossing tensors, or a polynomial contraction algorithm.

An actionable alternative must change an explicit assumption: for example,
give a different exact encoding or a different jointly tractable target
family, and prove preservation of the original decision together with the
full evaluation cost. Repeating a finer grid search for one common 2 by 2
basis of these two pairs cannot overcome the exact obstruction.

## Reproduction and limits

Run `python -m unittest -v test_basis.py` and `python run_experiments.py`
from this directory. `basis.py` and the certificate replay use only the
standard library. The runner additionally uses SymPy for corroborating
Groebner computations; it records the installed version. RESULTS.json
stores complete polynomial systems, identities, graph data, exact values,
timings, and SHA-256 source hashes before and after the run.

The tests include 200 seeded rational basis matrices, all manually listed
polynomial formulas, branch coverage, parity/scaling actions, positive
graph signatures and certificate mutations. These bounded controls detect
implementation errors; the proof of nonexistence quantifies over all complex
bases and does not extrapolate from those tests. All tensor and graph
enumerations here have fixed small arity. No scalability claim is made.
