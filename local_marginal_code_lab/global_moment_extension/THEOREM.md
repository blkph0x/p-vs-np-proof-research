# A global degree-two moment constraint does not close the RM2 local gap

Status: written proof, with a separate-agent internal mathematical audit of
the degree-two repair and exact finite controls. This is not external referee
certification or formal verification.
Novelty is **UNKNOWN**. The relaxation below is explicitly a hybrid
`L_k + Boolean M_1`; it is not identified with a full Lasserre relaxation
of an unspecified parity encoding.

## Defined model and inherited construction

Let `C` be `RM(2,m)` pinned to value one at coordinate zero. There are
\(N=2^m-1\) nonpin variables \(x_i\). Let \(L_k(C)\) be the
projection-marginal LP defined in the
[hierarchy note](../LOCAL_MARGINAL_HIERARCHY_NOTE.md): normalized,
nonnegative tables on every scope of total size at most \(k\), supported
on the exact projections of the pinned code, consistent on containments.

For such a point, let \(y_\varnothing=1\) and
\(y_A=\widetilde{\mathbb E}\prod_{i\in A}x_i\), as read from its local
tables. The Boolean moment matrix of order one is indexed by
\(\varnothing,\{1\},\ldots,\{N\}\):
\[
 (M_1)_{A,B}=y_{A\cup B}.
\]
The union implements \(x_i^2=x_i\). Define, without ambiguity,
\[
 H_{k,1}(C)=\{\,y\in L_k(C):M_1(y)\succeq0\,\}. \tag{1}
\]
Only this hybrid is asserted feasible below.
Including the fixed pin in the matrix merely duplicates the constant row
and column, so it does not change this positive-semidefiniteness condition.

The [virtual-dimension theorem](../REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md)
provides feasible local tables through \(k=D+4\), for \(m\ge D\ge3\),
with moments
\[
 y_A^{(0)}=\frac{G(D-\operatorname{rank}A)}{G(D)},\qquad
 G(t)={t\brack2}_2=
 \begin{cases}(2^t-1)(2^t-2)/6&t\ge2,\\0&t<2.\end{cases} \tag{2}
\]
It supplies the all-scope nonnegativity and pinned-support proof; this
note does not infer those conclusions from the finite controls.
Set
\[
 Q=2^D-1,\qquad a=2^{D-2}-1=(Q-3)/4.
\]
Every distinct pair of nonzero binary vectors is linearly independent.
Consequently the common first and second moments are
\[
 p=\frac aQ,\qquad q=\frac{a(a-1)}{Q(Q-1)}. \tag{3}
\]
Write \(T=\sum_{i=1}^N x_i\). The integer minimum of \(1+T\) on the
pinned code is \(I=2^{m-2}=(N+1)/4\), attained by a codimension-two
subspace indicator. These are the standard RM minimum-distance facts;
see [Santi, Häger, Pfister, Section II](https://arxiv.org/pdf/1804.10319).

## The original witness has exactly one negative moment eigenvalue

Its first two total-weight moments give
\[
 V_0=\widetilde{\mathbb E}(T-Np)^2
    =Np+N(N-1)q-N^2p^2
    =Np(1-p)\frac{Q-N}{Q-1}. \tag{4}
\]
For \(m>D\), this is negative. Thus this particular witness fails
the single degree-two square \((T-Np)^2\).

Its entire matrix has the form
\[
 M_1^{(0)}=
 \begin{pmatrix}
 1&p\mathbf1^T\\
 p\mathbf1&(p-q)I+qJ
 \end{pmatrix},\qquad J=\mathbf1\mathbf1^T.
\]
There are \(N-1\) contrast eigenvalues \(p-q>0\). The remaining two
are the eigenvalues of the real symmetric matrix
\[
 \begin{pmatrix}1&\sqrt Np\\\sqrt Np&b\end{pmatrix},
 \qquad b=p+(N-1)q,
\]
namely
\[
 \lambda_\pm=\frac{1+b\pm\sqrt{(1-b)^2+4Np^2}}2. \tag{5}
\]
Their product is \(b-Np^2=V_0/N\), so exactly one is negative for
\(m>D\). An actual negative eigenvector in the original coordinates is
\[
 \left(-\frac{Np}{1-\lambda_-},1,\ldots,1\right).
\]
The rational vector \((-Np,1,\ldots,1)\) is a negative quadratic-form
certificate of value \(V_0\); it need not itself be an eigenvector.

## A feasible repair of the whole matrix, with a remaining objective gap

Mix every local table in (2) with the restriction of the genuine all-ones
codeword. Use the same coefficient on every scope:
\[
 \beta=\frac{p(N-Q)}{N(Q-1)(1-p)}
       =\frac{a(N-Q)}{N(Q-1)(Q-a)}. \tag{6}
\]
For \(m>D\ge3\), \(0<\beta<1\); for \(m=D\), \(\beta=0\).
The strict upper bound follows, for example, from
\(\beta<a/((Q-1)(Q-a))<1\).
This mixture preserves normalization, nonnegativity, all containment
equalities, and exact pinned-code projection support. Its moments are
\[
 y_A^*=(1-\beta)y_A^{(0)}+\beta. \tag{7}
\]
This also gives \(y_\varnothing^*=1\). Write \(p^*,q^*\) for the first
two moments and \(F=Np^*\) for the reduced objective.

The mixture variance is the polynomial identity
\[
 V_\beta=(1-\beta)\bigl[V_0+\beta N^2(1-p)^2\bigr]. \tag{8}
\]
Substitution of (6) gives \(V_\beta=0\).
Its covariance Schur complement is
\[
 (p^*-q^*)I+(q^*-(p^*)^2)J
   =(p^*-q^*)(I-J/N).
\]
Here \(\alpha=p^*-q^*=(1-\beta)(p-q)>0\).
In particular the following is an exact Gram decomposition:
\[
 M_1^*=
\begin{pmatrix}1\\p^*\mathbf1\end{pmatrix}
\begin{pmatrix}1\\p^*\mathbf1\end{pmatrix}^{T}
+\alpha
 \begin{pmatrix}0&0\\0&I-J/N\end{pmatrix}\succeq0. \tag{9}
\]
The eigenvalues are \(\alpha\), with multiplicity \(N-1\);
\(1+N(p^*)^2\); and zero. Its null vector is
\((-F,1,\ldots,1)\).
More generally, among mixtures of this original witness and the
all-ones codeword with coefficient in \([0,1]\), (6) is the smallest
coefficient making \(M_1\) positive semidefinite: (8) determines the
sign of the remaining Schur eigenvalue.
This is a minimum within a specified one-parameter family, not a
claim to optimize the hybrid relaxation.

The objective simplifies to
\[
 F=\frac{a(N-1)}{Q-1},\qquad W=1+F,\qquad
 I-W=\frac{N-Q}{2(Q-1)}>0\quad(m>D). \tag{10}
\]
Therefore \(H_{D+4,1}(C)\) has a strictly fractional optimum:
its optimum is at most \(W<I\). A full degree-two Boolean moment
constraint does not close the actual objective gap of this hybrid.
No matching hybrid lower bound is asserted.

For fixed \(D\) and \(m\) tending to infinity, the exhibited ratio
\(I/W\) tends to \((Q-1)/(Q-3)>1\). For \(D=m-1\), the exhibited
additive gap tends to \(1/2\), while its ratio tends to one.
Neither asymptotic statement describes an unknown exact hybrid optimum.

## The repaired witness fails an explicit degree-four square

This additional calculation prevents interpreting (9) as feasibility
for higher-order moment matrices.
Let \(r=G(D-3)/G(D)\), and \(r^*=(1-\beta)r+\beta\).
For distinct points \(u,v\), exactly one further point, \(u+v\), has
rank two with them. The other \(N-3\) points give rank three. Thus
\[
 \widetilde{\mathbb E}^*[T x_u x_v]
       =3q^*+(N-3)r^*.
\]
Put \(L=T-F\). Equations (3), (6), and (7) give
\[
 \begin{split}
 c&=\widetilde{\mathbb E}^*[Lx_ux_v]
     =3q^*+(N-3)r^*-Fq^*\\
  &=\frac{(N-Q)(Q+1)(3NQ-N+Q-3)}
          {32N(Q-1)^3}>0 \qquad(m>D).
 \end{split} \tag{11}
\]
For an algebraic check one may use
\(r=q(a-3)/(Q-3)\), valid also at \(D=3\) because \(q=0\).
Now \(q^*>0\), \(\widetilde{\mathbb E}^*L^2=0\), and Boolean
reduction gives \((x_ux_v)^2=x_ux_v\). Consequently
\[
 \widetilde{\mathbb E}^*
 \left(L-\frac{c}{q^*}x_ux_v\right)^2=-\frac{c^2}{q^*}<0. \tag{12}
\]
This is a literal square of a degree-two polynomial, so its degree is
at most four. It excludes this repaired sequence from the full Boolean
moment matrix \(M_2\). It does **not** show that adding \(M_2\) to the
local LP makes its optimum integral: different feasible moments could
survive. Determining that optimum requires a new certificate or a new
feasible construction.

## Relation to named hierarchies and existing results

For a specified polynomial formulation with Boolean equations and declared
code constraints, an order-\(r\) moment/SOS relaxation uses moments through
degree \(2r\), positivity for squares of polynomials of degree at most \(r\),
and the appropriate constraints/localizing conditions from that
formulation. Thus its moment component contains \(M_1\succeq0\) when
\(r\ge1\), and \(M_2\succeq0\) when \(r\ge2\).
The standard definitions are in
[Laurent, Sections 4.1.3–4.1.5 and 6.1](https://homepages.cwi.nl/~monique/files/moment-ima-update-new.pdf).

The extensional support rules in \(L_k\) can contain consequences of all
global code constraints. They are not automatically the localizing
constraints of a sparse parity polynomial encoding, and that encoding's
constraint degrees affect the first admissible order. This note proves
neither direction of an unqualified equality between the hybrid (1) and
a named Lasserre level. Statements (4) and (12), in contrast, violate
explicit square positivity regardless of those additional constraints.

The earlier [finite SOS audit](../REED_MULLER_SOS_MOMENT_REPORT.md)
already establishes (4) for \(D=4,m=5\):
\(V_0=-992/175\). The earlier
[one-square optimization certificate](../REED_MULLER_SOS_STRENGTHENED_REPORT.md)
has reduced optimum \(7037/1095\) after adding its particular square.
The present repaired point at those parameters has
\[
 \beta=2/217,\qquad F=45/7,\qquad W=52/7,\qquad I-W=4/7.
\]
The two objective values are compatible: that earlier model imposes one
chosen square, while this point satisfies all degree-two squares. The
finite separation is inherited; the all-parameter algebraic extension
and repair are proved here without a novelty claim.

## Finite validation and costs

`moments.py` uses exact integers and fractions. `test_global_moment.py`
independently checks dense positive semidefiniteness by rational
elimination, the Gram identity entry by entry, genuine codimension-two
subspace averages, direct monomial expansion of the negative squares,
and local tables against actual quadratic-polynomial projection spans.
Tests include below-threshold mixtures, tampered matrix entries,
the genuine \(m=D\) boundary, strict types, and allocation guards.

The scalar formulas require polynomial bit work in \(D+m\), without
allocating \(N\) coordinates. A dense matrix has \((N+1)^2\) entries;
its constructor is explicitly capped. A local table has \(2^{|S|}\)
atoms and is separately capped. No polynomial-in-code-length algorithm
for constructing every scope is claimed by the formula tests, and no
algorithm for general SAT or a P-versus-NP conclusion is supplied.

Replay from this directory:

```text
python -m unittest -v test_global_moment.py
python run_experiments.py
```
