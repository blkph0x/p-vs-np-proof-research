# Exact linear-information frontier and order certificates

For a binary parity system $Ax=b$, let $P$ be the variables before a cut and
$S$ the variables after it. Write $U=\operatorname{im}(A_P)$ and
$V=\operatorname{im}(A_S)$. A prefix with assignment $p$ leaves the residual
equation

\[
A_Ss=b+A_Pp.
\]

Distinct consistent right-hand sides have disjoint solution sets, and the
reachable right-hand sides form an affine coset of $U\cap V$. Therefore the
number of live residual classes is

\[
2^{\lambda(P)},\qquad
\lambda(P)=\operatorname{rank}(A_P)+\operatorname{rank}(A_S)-\operatorname{rank}(A).
\]

The new executable oracle computes this rank exactly and uses subset dynamic
programming to minimize the maximum $\lambda$ over all variable orders. The
certificate contains the order and every cut's three ranks; an independent
replay recomputes both the cut values and the optimum DP.

## Adversarial ordering control

For $m$ independent crossing equations

\[
x_i\oplus y_i=0\qquad(0\leq i<m),
\]

the order $x_0,\ldots,x_{m-1},y_0,\ldots,y_{m-1}$ has midpoint width $m$.
The interleaved order $x_0,y_0,x_1,y_1,\ldots$ has width one: at every cut,
at most one equation is split between past and future. For $m=6$, the saved
certificate verifies widths 6 and 1 on the same matrix.

Repeated identical parity rows have width one in every order, while identity
rows have width zero. These controls separate redundant information from a
genuine layout obstruction.

The subset optimizer is exponential in the number of variables. It is a
proof-producing oracle for small systems, not a polynomial minimum-width
algorithm for arbitrary SAT. A universal route would still need a scalable
order/width certificate and a way to handle non-affine constraints.
