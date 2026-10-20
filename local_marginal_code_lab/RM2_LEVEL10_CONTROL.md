# A ten-coordinate obstruction and an explicit lower bound

Status: written derivation with exact finite tests. This note is not a
proof-assistant verification or a determination of the full level-ten optimum.
Novelty is **UNKNOWN**. It makes no claim about P versus NP.

This uses the definitions, symmetrization, atom types, and proved compact
identity in [the level-nine theorem](REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md).
For \(C=RM(2,m)\), pin coordinate zero to one and put a consistent normalized
nonnegative table, supported on the pinned code projection, on every scope
of **total size at most ten**. Call this \(L_{10}\). Write \(F\) for the sum
of nonpin singleton probabilities and \(W=1+F\).

## A Boolean inequality on an explicit scope

For \(m\ge6\), embed the following coordinates from \(\mathbb F_2^6\):
\[
 S=\{1,2,4,8,12,16,20,24,28,32\},\qquad B=\{1,2\}.
\]
Integers denote binary coordinate vectors. The eight members of
\(T=S\setminus B\) occupy distinct nonzero cosets modulo
\(\langle1,2\rangle\). Thus every \(\{1,2,a\}\), \(a\in T\), has rank
three, and every \(\{1,2,a,b\}\), \(a\ne b\in T\), has rank four.
The entire scope has rank six. These facts, rather than the integer
labels themselves, are the needed geometric conditions.

For any Boolean assignment on \(S\), let
\(E=x_1x_2\) and \(t=\sum_{a\in T}x_a\). Then
\[
 E\left(1-t+\binom t2\right)
   =E\,\frac{(t-1)(t-2)}2\ \ge0. \tag{1}
\]
This holds for every integer \(0\le t\le8\), regardless of code support.
Average a feasible \(L_{10}\) solution over \(GL(m,2)\), which preserves
the pin, locality, support, and objective. Let \(p,q,r,v\) denote the
common moments of one, two, three independent, and four independent
nonzero points, respectively. Taking the expectation of (1) gives
\[
 C:=q-8r+28v\ge0. \tag{2}
\]
The table needed for this argument has ten **nonpin** coordinates, hence
total size ten. No eleven-coordinate table including the pin is required.
Support is still the projection of the globally pinned code, as in the
definition of the relaxation.

## The entire level-nine optimum is excluded

Use the level-nine notation \(a=z_{10}\),
\(s_N=z_8-b_N\ge0\), and \(s_8=a-b_8\ge0\). Its proved identity is
\[
 279p-63=672z_2+1904b_P+8568b_N+4928b_6+216b_8
                    +952s_N+328s_8. \tag{3}
\]
If \(p=7/31\), every term on the right is zero. In particular
\[
 z_2=b_P=b_N=b_6=b_8=z_8=a=0.
\]
The mixed incidence equations give \(q=7b_2,\ r=b_2,\ v=0\).
The base incidence identities
\[
 z_8=\frac a7-\frac c4+\frac q8-\frac p{56},\qquad
 v=\frac{2a}7+\frac{3r}2-\frac c4-\frac{5q}8+\frac{5p}{56}
\]
then imply \(p=7q-14r=35b_2\). Therefore
\[
 q=\frac7{155},\qquad r=\frac1{155},\qquad v=0,
 \qquad C=-\frac1{155}<0.
\]
This excludes every symmetrized feasible \(L_{10}\) point attaining the
level-nine objective. An unsymmetrized point at the same objective would
average to such a point, so it is also excluded. This is stronger than
merely showing that the displayed level-nine upper witness fails.

## A quantitative bound without an optimizer

The same incidence identities yield an explicit rational bound.
Eliminating \(c\) from the two base identities above gives
\[
 p=\frac{28}3v-\frac43a-14r+7q-\frac{28}3z_8.
\]
Substitute the mixed incidence equations from the level-nine theorem:
\[
\begin{aligned}
 q&=7b_2+7b_P+28b_N+21b_6+b_8,\\
 r&=b_2+3b_P+12b_N+15b_6+b_8,\\
 v&=b_P+4b_N+10b_6+b_8.
\end{aligned}
\]
Equation (2) consequently reads
\[
 C=-b_2+11b_P+44b_N+181b_6+21b_8.
\]
Eliminating \(b_2\), and replacing \(a=b_8+s_8\) and \(z_8=b_N+s_N\),
gives
\[
 p=\frac{1204}3b_P+1596b_N+\frac{19096}3b_6+736b_8
          -35C-\frac{28}3s_N-\frac43s_8.
\]
Multiply (3) by 92 and subtract 27 times this last identity:
\[
\begin{split}
25641p-5796={}&61824z_2+164332b_P+745164b_N+281512b_6\\
             &+87836s_N+30212s_8+945C\ \ge0. \tag{4}
\end{split}
\]
All seven quantities on the right are nonnegative in the stated model.
Hence, for every \(m\ge6\),
\[
 \boxed{\quad
 \min_{L_{10}}F\ \ge\frac{644(2^m-1)}{2849},\qquad
 \min_{L_{10}}W\ \ge1+\frac{644(2^m-1)}{2849}.
 \quad} \tag{5}
\]
The improvement is strict:
\[
 \frac{644}{2849}-\frac7{31}=\frac{21}{88319}>0.
\]
Equation (5) is a lower bound, **not an optimum formula**. No matching
full-\(L_{10}\) upper construction is supplied here. The coefficient 92
was chosen to cancel the \(b_8\) term in the combined identity; no claim
of best possible combination is needed.

## Direct failure of the old rank-moment construction

For comparison, the level-nine upper witness assigns
\[
155M_A=(155,35,7,1,0,\ldots)_{\operatorname{rank}(A)}.
\]
On the displayed \(S\), \(B=\{1,2\}\) is closed. The eight distinct
quotient directions give eight rank-three supersets of \(B\), each of
mass \(1/155\), and all rank-at-least-four moments vanish. Its formal
atom mass is therefore
\[
 \mu_S(B)=\frac7{155}-\frac8{155}=-\frac1{155}.
\]
The accompanying test also obtains this number directly by subset
inclusion-exclusion, independently of this closed-flat counting argument.

## A concrete next candidate, not an established extension

The existing level-eight and level-nine moments are the Gaussian
subspace-inclusion probabilities
\[
 M_A^{(D)}=
 \frac{\left[\begin{smallmatrix}D-\operatorname{rank}(A)\\2\end{smallmatrix}\right]_2}
      {\left[\begin{smallmatrix}D\\2\end{smallmatrix}\right]_2},
 \qquad D=4,\ 5,
\]
with value zero when the numerator's upper index is less than two.
For rank at most \(D\), this is literally the distribution of a uniform
codimension-two subspace in \(\mathbb F_2^D\). Extending these formal
moments to scopes of rank greater than \(D\) needs a separate proof.
Subspace avoidance and its Möbius inversion are classical; see the
Crapo–Rota Critical Theorem as stated in Section 7.1, Theorem 7.7 of
[Brändén and Leite](https://arxiv.org/html/2412.06595v3).
That theorem does not establish the virtual higher-rank extension here.

A precise falsifiable next question is whether \(D=6\),
\[
651M_A=(651,155,35,7,1,0,\ldots)_{\operatorname{rank}(A)},
\]
gives nonnegative, correctly supported tables on every nonpin scope of
size at most ten jointly with the pin, in every ambient dimension
\(m\ge6\). This would supply an upper bound with \(p=5/21\), not prove
that upper bound optimal. It passes the necessary row (2), with
\(C=7/651\). The test on this one scope is only a control, not an
all-scope result.

## Reproduction and limits of the tests

From this directory:

```text
python -m unittest -v test_rm2_level10_control
python -O -m unittest -v test_rm2_level10_control
```

The tests check all 1,024 assignments on the original ten-point scope,
all eight triples and 28 quadruples used by (2), the old witness's
negative atom by direct subset ranks, the equality-face consequences,
and the new bound as a rational row consequence of the independently
rebuilt historical geometry plus the new row. Deliberately missing pair
terms and incorrect coefficients are detected. A genuine codimension-two
subspace distribution in dimension six supplies a positive control.
They do not enumerate every ten-point configuration or certify a
full-level-ten optimum.
